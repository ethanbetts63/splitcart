from django.db import transaction
from products.models import Product, SKU
from data_management.database_updating_classes.product_updating.post_processing.product_enricher import ProductEnricher

class ProductManager:
    """
    Manages the creation and updating of Product and SKU objects using a memory-efficient,
    two-tier caching system. It resolves products using lightweight IDs and fetches
    full objects only when necessary for updates.
    """
    def __init__(self, command, caches, cache_updater, discovered_brand_pairs):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater
        self.discovered_brand_pairs = discovered_brand_pairs

    def _resolve_products(self, raw_product_data, company_obj):
        """
        Sorts raw product data into 'create' and 'update' lists using the lean cache.
        Returns lists of data for creation, tuples of (product_id, data) for updates,
        and tuples of (product_id or norm_string, sku_value) for SKU creation.
        """
        self.command.stdout.write("    - Resolving products and SKUs (create vs. update)...")
        products_to_create_data = []
        products_to_update_data = []  # Now stores (product_id, data)
        skus_to_create_tuples = []    # Stores (product_id or norm_string, sku_value)

        company_sku_cache = self.caches['products_by_sku'].get(company_obj.name, {})

        for data in raw_product_data:
            product_dict = data.get('product', {})
            if not product_dict:
                continue

            sku = product_dict.get('sku')
            matched_product_id = None
            
            # Tier 1: Barcode
            barcode = product_dict.get('barcode')
            if barcode and barcode in self.caches['products_by_barcode']:
                matched_product_id = self.caches['products_by_barcode'][barcode]

            # Tier 2: SKU (if no barcode match)
            if not matched_product_id and sku and sku in company_sku_cache:
                matched_product_id = company_sku_cache[sku]
            
            # Tier 3: Normalized String (if still no match)
            if not matched_product_id:
                norm_string = product_dict.get('normalized_name_brand_size')
                if norm_string and norm_string in self.caches['products_by_norm_string']:
                    matched_product_id = self.caches['products_by_norm_string'][norm_string]

            if matched_product_id:
                # Use the Tier 2 (ID-to-Data) cache to get necessary info
                canonical_product_data = self.caches['products_by_id'].get(matched_product_id)
                if not canonical_product_data:
                    self.command.stderr.write(self.command.style.ERROR(f"    - Consistency error: Product ID {matched_product_id} not found in products_by_id cache. Skipping."))
                    continue

                # Create an alias in the cache for downstream processes (like PriceManager)
                incoming_norm_string = product_dict.get('normalized_name_brand_size')
                canonical_norm_string = canonical_product_data['normalized_name_brand_size']
                if incoming_norm_string and canonical_norm_string and incoming_norm_string != canonical_norm_string:
                    self.cache_updater('products_by_norm_string', incoming_norm_string, matched_product_id)

                # If matched by barcode or SKU, check for brand variations
                if barcode or sku:
                    incoming_brand = product_dict.get('normalized_brand')
                    canonical_brand = canonical_product_data['brand_normalized_name']
                    if incoming_brand and canonical_brand and incoming_brand != canonical_brand:
                        self.discovered_brand_pairs.add((incoming_brand, canonical_brand))

                products_to_update_data.append((matched_product_id, data))
                
                # Check if a NEW SKU link needs to be created for this existing product
                if sku and sku not in company_sku_cache:
                    skus_to_create_tuples.append((matched_product_id, sku))
            else:
                products_to_create_data.append(data)
                # For new products, the SKU link will also be new
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
            
            raw_brand = product_dict.get('brand')
            company = metadata.get('company')
            initial_pairs = []
            if raw_brand and company:
                initial_pairs.append([raw_brand, company])

            new_product = Product(
                name=product_dict.get('name', ''),
                brand=None,  # Brand will be linked later by BrandManager
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
        Enriches existing Product objects using the ProductEnricher utility.
        `products_for_update_dict` contains the full, just-in-time fetched Product objects.
        """
        product_objects_to_update = []
        for product_id, data in products_to_update_data:
            existing_product = products_for_update_dict.get(product_id)
            if not existing_product:
                self.command.stderr.write(self.command.style.ERROR(f"    - Consistency error: Product ID {product_id} not found in just-in-time fetch. Skipping update."))
                continue

            product_dict = data['product']
            metadata = data['metadata']

            incoming_product_instance = Product(
                name=product_dict.get('name'),
                brand=None, # Brand is handled by BrandManager
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                size=product_dict.get('size'),
                sizes=product_dict.get('sizes', []),
                has_no_coles_barcode=product_dict.get('has_no_coles_barcode', False),
                aldi_image_url=product_dict.get('aldi_image_url'),
                url=product_dict.get('url'),
                brand_name_company_pairs=[[product_dict.get('brand'), metadata.get('company')]],
                normalized_name_brand_size_variations=[]
            )
            
            updated = ProductEnricher.enrich_canonical_product(
                canonical_product=existing_product,
                duplicate_product=incoming_product_instance
            )

            if updated:
                product_objects_to_update.append(existing_product)
        return product_objects_to_update

    def _update_caches(self, created_products, updated_products, new_skus, company_obj):
        """Updates the shared lean caches with new and updated product and SKU info."""
        self.command.stdout.write("    - Updating shared product and SKU caches...")
        
        # Process newly created products to populate all cache tiers
        for product in created_products:
            product_id = product.id
            brand_norm_name = product.brand.normalized_name if product.brand else None
            
            # Tier 2 cache: ID -> slim data dictionary
            self.caches['products_by_id'][product_id] = {
                'id': product_id,
                'normalized_name_brand_size': product.normalized_name_brand_size,
                'brand_normalized_name': brand_norm_name
            }
            # Tier 1 caches: key -> ID
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product_id)
            if product.normalized_name_brand_size:
                self.cache_updater('products_by_norm_string', product.normalized_name_brand_size, product_id)
        
        # Process updated products to ensure their Tier 2 data is fresh
        for product in updated_products:
            self.caches['products_by_id'][product.id]['normalized_name_brand_size'] = product.normalized_name_brand_size
            # Note: Brand updates are handled separately. This assumes the brand link doesn't change here.

        # Update SKU cache (Tier 1)
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

        # 1. Resolution (using lean caches)
        to_create_data, to_update_data, skus_to_create_tuples = self._resolve_products(raw_product_data, company_obj)

        # 2. Data Preparation for creations
        objects_to_create = self._prepare_creations(to_create_data)

        # 3. Just-in-Time Fetch for updates
        products_for_update_dict = {}
        if to_update_data:
            product_ids_to_update = list(set(pid for pid, data in to_update_data))
            self.command.stdout.write(f"    - Fetching {len(product_ids_to_update)} full product objects for update...")
            products_for_update = Product.objects.select_related('brand').filter(id__in=product_ids_to_update)
            products_for_update_dict = {p.id: p for p in products_for_update}
        
        # 4. Data Preparation for updates
        objects_to_update = self._prepare_updates(to_update_data, products_for_update_dict)

        if not objects_to_create and not objects_to_update and not skus_to_create_tuples:
            self.command.stdout.write("    - No new or updated products or SKUs to persist.")
            return

        # 5. Persistence of Products
        newly_created_products = []
        try:
            with transaction.atomic():
                if objects_to_create:
                    self.command.stdout.write(f"    - Creating {len(objects_to_create)} new products...")
                    # Note: `brand` is not set here, it will be linked by BrandManager
                    Product.objects.bulk_create(objects_to_create, batch_size=500)
                
                if objects_to_update:
                    self.command.stdout.write(f"    - Updating {len(objects_to_update)} existing products...")
                    update_fields = [
                        'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                        'sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs'
                    ]
                    Product.objects.bulk_update(objects_to_update, update_fields, batch_size=500)

            # Re-fetch newly created products to get DB-assigned IDs and brand info for cache update
            if objects_to_create:
                norm_strings = [p.normalized_name_brand_size for p in objects_to_create]
                newly_created_products = list(Product.objects.select_related('brand').filter(normalized_name_brand_size__in=norm_strings))

            # 6. Data Preparation and Persistence of SKUs
            new_skus = []
            if skus_to_create_tuples:
                # Build a map of norm_string -> product_id for newly created products
                product_map = {p.normalized_name_brand_size: p.id for p in newly_created_products}
                
                skus_to_bulk_create = []
                for product_ref, sku_val in skus_to_create_tuples:
                    product_id = None
                    if isinstance(product_ref, int): # It's already a product_id
                        product_id = product_ref
                    else: # It's a norm_string for a new product
                        product_id = product_map.get(product_ref)
                    
                    if product_id:
                        skus_to_bulk_create.append(SKU(product_id=product_id, company=company_obj, sku=sku_val))
                    else:
                        self.command.stderr.write(self.command.style.ERROR(f"    - Could not find product ID for SKU creation: ref '{product_ref}'"))

                if skus_to_bulk_create:
                    self.command.stdout.write(f"    - Creating {len(skus_to_bulk_create)} new SKU links...")
                    with transaction.atomic():
                        new_skus = SKU.objects.bulk_create(skus_to_bulk_create, batch_size=500, ignore_conflicts=True)

            # 7. Cache Update (only after successful transactions)
            self._update_caches(newly_created_products, objects_to_update, new_skus, company_obj)

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing products or SKUs: {e}"))
            raise