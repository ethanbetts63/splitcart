from products.models import ProductBrand, Product
from django.db import transaction

class BrandManager:
    """
    Manages the creation, updating, and linking of ProductBrand objects.
    It is designed to work with the lean, two-tier caching system.
    """
    def __init__(self, command, caches, cache_updater, brand_translation_cache):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater
        self.brand_translation_cache = brand_translation_cache

    def process(self, processed_product_data_list, discovered_brand_pairs):
        """
        Uses discovered brand pairs to update brand variations, creates new brands,
        links products, and finally updates the master brand translation cache.
        """
        self.command.stdout.write("  - BrandManager: Processing brands...")

        if not processed_product_data_list:
            self.command.stdout.write("    - No products to process. Skipping.")
            return

        # --- Step 1 & 2: Analyze and Prepare DB Changes for Brands ---
        brands_to_update = {}
        temp_translation_updates = {}

        for incoming_brand, existing_brand_canonical in discovered_brand_pairs:
            canonical_name = self.brand_translation_cache.get(existing_brand_canonical, existing_brand_canonical)
            temp_translation_updates[incoming_brand] = canonical_name
            
            brand_obj = self.caches['normalized_brand_names'].get(canonical_name)
            if brand_obj:
                if brand_obj.id not in brands_to_update:
                    brands_to_update[brand_obj.id] = {
                        'obj': brand_obj,
                        'variations': set(brand_obj.normalized_name_variations or [])
                    }
                brands_to_update[brand_obj.id]['variations'].add(incoming_brand)

        all_brands_in_file = {p.get('product', {}).get('normalized_brand') for p in processed_product_data_list if p.get('product', {}).get('normalized_brand')}
        brands_to_create_names = set()

        for brand_name in all_brands_in_file:
            canonical_name = temp_translation_updates.get(brand_name, self.brand_translation_cache.get(brand_name, brand_name))
            if canonical_name not in self.caches['normalized_brand_names']:
                brands_to_create_names.add(canonical_name)
        
        brands_to_bulk_create = [
            ProductBrand(name=name, normalized_name=name, normalized_name_variations=[name])
            for name in brands_to_create_names
        ]
        
        brands_to_bulk_update = []
        for brand_id, update_data in brands_to_update.items():
            brand_obj = update_data['obj']
            new_variations = update_data['variations']
            if set(brand_obj.normalized_name_variations or []) != new_variations:
                brand_obj.normalized_name_variations = sorted(list(new_variations))
                brands_to_bulk_update.append(brand_obj)

        # --- Step 3: Database Operations for Brands ---
        with transaction.atomic():
            if brands_to_bulk_create:
                self.command.stdout.write(f"    - Creating {len(brands_to_bulk_create)} new brands.")
                ProductBrand.objects.bulk_create(brands_to_bulk_create, batch_size=500)
            
            if brands_to_bulk_update:
                self.command.stdout.write(f"    - Updating {len(brands_to_bulk_update)} existing brands.")
                ProductBrand.objects.bulk_update(brands_to_bulk_update, ['normalized_name_variations'], batch_size=500)
        
        if brands_to_bulk_create:
            newly_created_brands = ProductBrand.objects.filter(normalized_name__in=brands_to_create_names)
            for brand_obj in newly_created_brands:
                self.cache_updater('normalized_brand_names', brand_obj.normalized_name, brand_obj)

        # --- Step 4: Link Products to Brands (Refactored Logic) ---
        product_brand_links_to_make = {} # {product_id: brand_id}

        for product_data in processed_product_data_list:
            product_dict = product_data.get('product', {})
            normalized_brand = product_dict.get('normalized_brand')
            product_norm_string = product_dict.get('normalized_name_brand_size')

            if not normalized_brand or not product_norm_string:
                continue

            # Resolve the brand object
            canonical_name = temp_translation_updates.get(normalized_brand, self.brand_translation_cache.get(normalized_brand, normalized_brand))
            brand_obj = self.caches['normalized_brand_names'].get(canonical_name)
            
            # Resolve the product ID from the lean cache
            product_id = self.caches['products_by_norm_string'].get(product_norm_string)

            if product_id and brand_obj:
                product_brand_links_to_make[product_id] = brand_obj.id
        
        if product_brand_links_to_make:
            products_to_update_linking = []
            product_ids = list(product_brand_links_to_make.keys())
            
            # Just-in-time fetch for products that need linking
            products_from_db = Product.objects.filter(id__in=product_ids)
            
            for product in products_from_db:
                new_brand_id = product_brand_links_to_make[product.id]
                if product.brand_id != new_brand_id:
                    product.brand_id = new_brand_id
                    products_to_update_linking.append(product)
            
            if products_to_update_linking:
                self.command.stdout.write(f"    - Linking {len(products_to_update_linking)} products to their brands.")
                Product.objects.bulk_update(products_to_update_linking, ['brand'], batch_size=500)

        # --- Step 5: Update Master Translation Cache ---
        if temp_translation_updates:
            self.command.stdout.write(f"    - Applying {len(temp_translation_updates)} updates to the master brand translation cache.")
            self.brand_translation_cache.update(temp_translation_updates)
            
        self.command.stdout.write("  - BrandManager: Finished processing brands.")
