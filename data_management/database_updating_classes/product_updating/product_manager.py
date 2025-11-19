from django.db import transaction
from products.models import Product, SKU
from data_management.database_updating_classes.product_updating.post_processing.product_enricher import ProductEnricher

class ProductManager:
    """
    Manages the creation and updating of Product and SKU objects.
    This class encapsulates the logic for resolving, enriching, mapping,
    persisting, and caching products and their company-specific SKUs.
    """
    def __init__(self, command, caches, cache_updater, discovered_brand_pairs):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater
        self.discovered_brand_pairs = discovered_brand_pairs

    def _resolve_products(self, raw_product_data, company_obj):
        """
        Sorts raw product data into 'create' and 'update' lists, and identifies
        new SKU relationships to be created.
        """
        self.command.stdout.write("    - Resolving products and SKUs (create vs. update)...")
        products_to_create_data = []
        products_to_update_data = []
        skus_to_create_tuples = [] # List of (Product object or norm_string, sku_value)

        company_sku_cache = self.caches['products_by_sku'].get(company_obj.name, {})
        # This set tracks barcodes of NEW products identified in this file
        # to prevent duplicate creation attempts from the same file.
        barcodes_for_creation = set()

        for data in raw_product_data:
            product_dict = data.get('product', {})
            if not product_dict:
                continue

            sku = product_dict.get('sku')
            barcode = product_dict.get('barcode')
            norm_string = product_dict.get('normalized_name_brand_size')
            match = None
            
            # Tier 1: Barcode
            if barcode and barcode in self.caches['products_by_barcode']:
                match = self.caches['products_by_barcode'][barcode]

            # Tier 2: SKU (if no barcode match)
            if not match and sku and sku in company_sku_cache:
                match = company_sku_cache[sku]
            
            # Tier 3: Normalized String (if still no match)
            if not match and norm_string and norm_string in self.caches['products_by_norm_string']:
                match = self.caches['products_by_norm_string'][norm_string]

            # Tier 4: Check if this is a duplicate of a product being created in this same file
            if not match and barcode and barcode in barcodes_for_creation:
                # This is a duplicate within the same file. We can't assign it an ID yet,
                # but we can treat it as a match to prevent it from being created again.
                # We find its canonical norm_string to create an alias.
                # For simplicity, we can just skip it or log it, as the first one will be created.
                # Let's create an alias for downstream price processing.
                canonical_norm_string = next(
                    (p['product'].get('normalized_name_brand_size') for p in products_to_create_data 
                     if p['product'].get('barcode') == barcode), None)
                if canonical_norm_string:
                    self.cache_updater('products_by_norm_string', norm_string, self.caches['products_by_norm_string'].get(canonical_norm_string))
                continue # Skip to next item to avoid adding to any list

            if match: # match is now a product_id (int)
                # If a match is found, there's a chance the incoming normalized string is a variation.
                # We create an alias in the cache so that this variation string can be resolved
                # by downstream processes (like PriceManager).
                incoming_norm_string = product_dict.get('normalized_name_brand_size')
                canonical_norm_string = self.caches['products_by_id'][match]['normalized_name_brand_size']
                if incoming_norm_string and canonical_norm_string and incoming_norm_string != canonical_norm_string:
                    # Cache the incoming_norm_string to point to the product_id of the canonical product
                    self.cache_updater('products_by_norm_string', incoming_norm_string, match)

                # If matched by barcode or SKU, check for brand variations
                if barcode or sku:
                    incoming_brand = product_dict.get('normalized_brand')
                    canonical_brand = self.caches['products_by_id'][match]['brand_normalized_name']
                    if incoming_brand and canonical_brand and incoming_brand != canonical_brand:
                        # The pair is directional: (incoming, existing)
                        pair = (incoming_brand, canonical_brand)
                        self.discovered_brand_pairs.add(pair)

                products_to_update_data.append((match, data)) # match is product_id (int)
                # If we found an existing product, we still need to check if a NEW SKU link needs to be created for it.
                if sku and sku not in company_sku_cache:
                    skus_to_create_tuples.append((match, sku)) # match is product_id (int)
            else:
                # This is a new product. Add its barcode to our tracking set for this file.
                if barcode:
                    barcodes_for_creation.add(barcode)
                
                products_to_create_data.append(data)
                # For new products, the SKU link will also be new.
                if sku:
                    skus_to_create_tuples.append((norm_string, sku)) # norm_string as placeholder for new product's ID
        
        self.command.stdout.write(f"      - Products to create: {len(products_to_create_data)}, Products to update: {len(products_to_update_data)}")
        self.command.stdout.write(f"      - SKU links to create: {len(skus_to_create_tuples)}")
        return products_to_create_data, products_to_update_data, skus_to_create_tuples

    def _prepare_creations(self, products_to_create_data):
        """Maps raw data dictionaries to new Product model instances."""
        product_objects_to_create = []
        for data in products_to_create_data:
            product_dict = data['product']
            metadata = data['metadata']
            
            raw_brand = product_dict.get('brand')
            company = metadata.get('company')
            initial_pairs = []
            if raw_brand and company:
                initial_pairs.append([raw_brand, company])

            new_product = Product(
                name=product_dict.get('name', ''),
                brand=None, # Brand will be linked later by BrandManager
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                size=product_dict.get('size'),
                sizes=product_dict.get('sizes', []),
                has_no_coles_barcode=product_dict.get('has_no_coles_barcode', False),
                aldi_image_url=product_dict.get('aldi_image_url'),
                url=product_dict.get('url'),
                brand_name_company_pairs=initial_pairs
            )
            product_objects_to_create.append(new_product)
        return product_objects_to_create

    def _prepare_updates(self, products_to_update_data, products_for_update_dict):
        """
        Enriches existing Product objects using the ProductEnricher utility
        and returns a list of those that were actually changed.
        """
        product_objects_to_update = []
        for product_id, data in products_to_update_data:
            product_dict = data['product']
            metadata = data['metadata']

            existing_product = products_for_update_dict.get(product_id)
            if not existing_product:
                self.command.stderr.write(self.command.style.ERROR(f"    - Error: Full Product object not found for ID {product_id}. Skipping update."))
                continue

            # Create a temporary, in-memory Product instance from the incoming data
            # to use the generic ProductEnricher utility.
            brand_obj = None # Brand is set to None as it's handled by BrandManager
            
            incoming_product_instance = Product(
                name=product_dict.get('name'),
                brand=brand_obj,
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                size=product_dict.get('size'),
                sizes=product_dict.get('sizes', []),
                has_no_coles_barcode=product_dict.get('has_no_coles_barcode', False),
                aldi_image_url=product_dict.get('aldi_image_url'),
                url=product_dict.get('url'),
                brand_name_company_pairs=[[product_dict.get('brand'), metadata.get('company')]],
                normalized_name_brand_size_variations=product_dict.get('normalized_name_brand_size_variations', []) # Bug fix
            )
            # Use the centralized enricher to merge the data
            updated = ProductEnricher.enrich_canonical_product(
                canonical_product=existing_product,
                duplicate_product=incoming_product_instance
            )

            if updated:
                product_objects_to_update.append(existing_product)
        return product_objects_to_update

    def _update_caches(self, created_products, updated_products, new_skus, company_obj):
        """Updates the shared caches with new and updated product and SKU info."""
        self.command.stdout.write("    - Updating shared product and SKU caches...")
        products_to_process = created_products + updated_products
        
        for product in products_to_process:
            # Update the products_by_id cache with the full lean product info
            self.cache_updater('products_by_id', product.id, {
                'id': product.id,
                'normalized_name_brand_size': product.normalized_name_brand_size,
                'brand_normalized_name': product.brand.normalized_name if product.brand else None
            })
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product.id)
            if product.normalized_name_brand_size:
                self.cache_updater('products_by_norm_string', product.normalized_name_brand_size, product.id)
        
        # Update SKU cache
        company_name = company_obj.name
        if company_name not in self.caches['products_by_sku']:
            self.caches['products_by_sku'][company_name] = {}
        
        for sku_obj in new_skus:
            self.caches['products_by_sku'][company_name][sku_obj.sku] = sku_obj.product_id

        self.command.stdout.write("      - Caches updated.")

    def process(self, raw_product_data, company_obj):
        """
        Creates and updates products and SKUs based on the raw data.
        """
        self.command.stdout.write("  - ProductManager: Processing products...")

        # 1. Resolution
        to_create_data, to_update_data, skus_to_create_tuples = self._resolve_products(raw_product_data, company_obj)

        # 2. Data Preparation for Products
        objects_to_create = self._prepare_creations(to_create_data)
        
        products_for_update_dict = {}
        if to_update_data:
            # Collect all unique product_ids that need to be updated
            product_ids_to_update = {item[0] for item in to_update_data} # item[0] is product_id
            
            # Fetch full Product objects in a single query
            full_products_to_update = Product.objects.filter(id__in=list(product_ids_to_update))
            products_for_update_dict = {p.id: p for p in full_products_to_update}

        objects_to_update = self._prepare_updates(to_update_data, products_for_update_dict)

        if not objects_to_create and not objects_to_update and not skus_to_create_tuples:
            self.command.stdout.write("    - No new or updated products or SKUs to persist.")
            return

        # 3. Persistence of Products
        newly_created_products = []
        try:
            with transaction.atomic():
                if objects_to_create:
                    self.command.stdout.write(f"    - Creating {len(objects_to_create)} new products...")
                    Product.objects.bulk_create(objects_to_create, batch_size=500)
                
                if objects_to_update:
                    self.command.stdout.write(f"    - Updating {len(objects_to_update)} existing products...")
                    update_fields = [
                        'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                        'sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs'
                    ]
                    Product.objects.bulk_update(objects_to_update, update_fields, batch_size=500)

            # Re-fetch newly created products to get their DB-assigned IDs
            # bulk_create often doesn't return objects with IDs, so a re-fetch is safer.
            newly_created_products_list = []
            if objects_to_create:
                norm_strings_for_new_products = [p.normalized_name_brand_size for p in objects_to_create]
                newly_created_products_list = list(Product.objects.filter(normalized_name_brand_size__in=norm_strings_for_new_products))
            
            # Build product_map: product_id -> Product object
            # This map will be used to link SKUs to products.
            # Start with all the products that were matched for potential updates.
            product_map = products_for_update_dict.copy()
            # Add the newly created products.
            for p in newly_created_products_list:
                product_map[p.id] = p
            
            # 4. Data Preparation and Persistence of SKUs
            new_skus = []
            if skus_to_create_tuples:
                skus_to_bulk_create = []
                for product_ref, sku_val in skus_to_create_tuples:
                    product_obj = None
                    if isinstance(product_ref, int): # It's a product_id for an existing product
                        product_obj = product_map.get(product_ref)
                    else: # It's a norm_string for a new product, we need to find its ID after creation
                        # Find the product object from newly_created_products_list by its norm_string
                        product_obj = next((p for p in newly_created_products_list if p.normalized_name_brand_size == product_ref), None)
                    
                    if product_obj:
                        skus_to_bulk_create.append(SKU(product=product_obj, company=company_obj, sku=sku_val))
                    else:
                        self.command.stderr.write(self.command.style.ERROR(f"    - Could not find product for SKU creation: ref '{product_ref}'"))

                if skus_to_bulk_create:
                    self.command.stdout.write(f"    - Creating {len(skus_to_bulk_create)} new SKU links...")
                    with transaction.atomic():
                        new_skus = SKU.objects.bulk_create(skus_to_bulk_create, batch_size=500, ignore_conflicts=True)

            # 5. Cache Update (only after successful transactions)
            self._update_caches(newly_created_products, objects_to_update, new_skus, company_obj)

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing products or SKUs: {e}"))
            raise