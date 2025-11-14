from django.db import transaction
from products.models import Product, SKU
from data_management.database_updating_classes.product_updating.post_processing.product_enricher import ProductEnricher

class ProductManager:
    """
    Manages the creation and updating of Product and SKU objects.
    This class encapsulates the logic for resolving, enriching, mapping,
    persisting, and caching products and their company-specific SKUs.
    """
    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

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

        for data in raw_product_data:
            product_dict = data.get('product', {})
            if not product_dict:
                continue

            sku = product_dict.get('sku')
            match = None
            
            # Tier 1: Barcode
            barcode = product_dict.get('barcode')
            if barcode and barcode in self.caches['products_by_barcode']:
                match = self.caches['products_by_barcode'][barcode]

            # Tier 2: SKU (if no barcode match)
            if not match and sku and sku in company_sku_cache:
                match = company_sku_cache[sku]
            
            # Tier 3: Normalized String (if still no match)
            if not match:
                norm_string = product_dict.get('normalized_name_brand_size')
                if norm_string and norm_string in self.caches['products_by_norm_string']:
                    match = self.caches['products_by_norm_string'][norm_string]

            if match:
                # If a match is found, there's a chance the incoming normalized string is a variation.
                # We update the raw data in-memory to use the canonical normalized string.
                # This ensures the PriceManager can find the product in the cache.
                incoming_norm_string = product_dict.get('normalized_name_brand_size')
                canonical_norm_string = match.normalized_name_brand_size
                if incoming_norm_string and canonical_norm_string and incoming_norm_string != canonical_norm_string:
                    data['product']['normalized_name_brand_size'] = canonical_norm_string

                products_to_update_data.append((match, data))
                # If we found an existing product, we still need to check if a NEW SKU link needs to be created for it.
                if sku and sku not in company_sku_cache:
                    skus_to_create_tuples.append((match, sku))
            else:
                products_to_create_data.append(data)
                # For new products, the SKU link will also be new.
                if sku:
                    norm_string = product_dict.get('normalized_name_brand_size')
                    skus_to_create_tuples.append((norm_string, sku))
        
        self.command.stdout.write(f"      - Products to create: {len(products_to_create_data)}, Products to update: {len(products_to_update_data)}")
        self.command.stdout.write(f"      - SKU links to create: {len(skus_to_create_tuples)}")
        return products_to_create_data, products_to_update_data, skus_to_create_tuples

    def _prepare_creations(self, products_to_create_data):
        """Maps raw data dictionaries to new Product model instances."""
        product_objects_to_create = []
        for data in products_to_create_data:
            product_dict = data['product']
            metadata = data['metadata']
            
            normalized_brand = product_dict.get('normalized_brand')
            brand_obj = None # Initialize brand_obj to None

            if normalized_brand: # Only try to look up a brand if normalized_brand is not None/empty
                brand_obj = self.caches['normalized_brand_names'].get(normalized_brand)
                if not brand_obj:
                    # This means normalized_brand had a value, but it wasn't in the cache.
                    # This is a genuine error, so we should skip.
                    self.command.stderr.write(self.command.style.ERROR(f"      - ERROR: Brand '{normalized_brand}' not found in cache. Skipping product '{product_dict.get('name')}'.'"))
                    continue
            # If normalized_brand was None/empty, brand_obj remains None, which is allowed by the Product model.

            new_product = Product(
                name=product_dict.get('name', ''),
                brand=brand_obj, # This will be None if no brand was found or provided
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                size=product_dict.get('size'),
                sizes=product_dict.get('sizes', []),
                has_no_coles_barcode=product_dict.get('has_no_coles_barcode', False),
                aldi_image_url=product_dict.get('aldi_image_url'),
                url=product_dict.get('url'),
                brand_name_company_pairs=[[product_dict.get('brand'), metadata.get('company')]]
            )
            product_objects_to_create.append(new_product)
        return product_objects_to_create

    def _prepare_updates(self, products_to_update_data):
        """
        Enriches existing Product objects using the ProductEnricher utility
        and returns a list of those that were actually changed.
        """
        product_objects_to_update = []
        for existing_product, data in products_to_update_data:
            product_dict = data['product']
            metadata = data['metadata']

            # Create a temporary, in-memory Product instance from the incoming data
            # to use the generic ProductEnricher utility.
            # We need to fetch the brand object from the cache for this.
            brand_obj = self.caches['normalized_brand_names'].get(product_dict.get('normalized_brand'))
            
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
                # The variation list of the incoming product itself is not needed
                # as its own nnbs is what we are adding as a variation.
                normalized_name_brand_size_variations=[] 
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
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product)
            if product.normalized_name_brand_size:
                self.cache_updater('products_by_norm_string', product.normalized_name_brand_size, product)
        
        # Update SKU cache
        company_name = company_obj.name
        if company_name not in self.caches['products_by_sku']:
            self.caches['products_by_sku'][company_name] = {}
        
        for sku_obj in new_skus:
            self.caches['products_by_sku'][company_name][sku_obj.sku] = sku_obj.product

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
        objects_to_update = self._prepare_updates(to_update_data)

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
            if objects_to_create:
                norm_strings = [p.normalized_name_brand_size for p in objects_to_create]
                newly_created_products = list(Product.objects.filter(normalized_name_brand_size__in=norm_strings))

            # 4. Data Preparation and Persistence of SKUs
            new_skus = []
            if skus_to_create_tuples:
                product_map = {p.normalized_name_brand_size: p for p in newly_created_products}
                for p in objects_to_update: # Add updated products to map
                    product_map[p.normalized_name_brand_size] = p
                for p, _ in to_update_data: # Add matched products to map
                    product_map[p.normalized_name_brand_size] = p

                skus_to_bulk_create = []
                for product_ref, sku_val in skus_to_create_tuples:
                    product_obj = None
                    if isinstance(product_ref, Product):
                        product_obj = product_ref
                    else: # It's a norm_string for a new product
                        product_obj = product_map.get(product_ref)
                    
                    if product_obj:
                        skus_to_bulk_create.append(SKU(product=product_obj, company=company_obj, sku=sku_val))
                    else:
                        self.command.stderr.write(self.command.style.ERROR(f"    - Could not find product for SKU creation: ref '{product_ref}'"))

                if skus_to_bulk_create:
                    self.command.stdout.write(f"    - Creating {len(skus_to_bulk_create)} new SKU links...")
                    with transaction.atomic():
                        # ignore_conflicts=True because in a race condition, another process might create it.
                        new_skus = SKU.objects.bulk_create(skus_to_bulk_create, batch_size=500, ignore_conflicts=True)

            # 5. Cache Update (only after successful transactions)
            self._update_caches(newly_created_products, objects_to_update, new_skus, company_obj)

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing products or SKUs: {e}"))
            raise