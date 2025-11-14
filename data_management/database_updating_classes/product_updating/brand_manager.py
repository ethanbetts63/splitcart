from products.models import ProductBrand, Product
from django.db import transaction

class BrandManager:
    """
    Manages the creation and updating of ProductBrand objects.
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

        # --- Step 1: Analyze and Plan DB Changes ---
        brands_to_update = {} # {brand_obj: set_of_new_variations}
        temp_translation_updates = {} # {variation: canonical}

        # Use discovered pairs to plan updates
        for incoming_brand, existing_brand_canonical in discovered_brand_pairs:
            # The canonical form is the one from the existing brand
            canonical_name = self.brand_translation_cache.get(existing_brand_canonical, existing_brand_canonical)
            temp_translation_updates[incoming_brand] = canonical_name
            
            brand_obj = self.caches['normalized_brand_names'].get(canonical_name)
            if brand_obj:
                if brand_obj not in brands_to_update:
                    brands_to_update[brand_obj] = set(brand_obj.name_variations or [])
                brands_to_update[brand_obj].add(incoming_brand)

        # Identify all brands needed for the file and find which ones need to be created
        all_brands_in_file = {p.get('product', {}).get('normalized_brand') for p in processed_product_data_list if p.get('product', {}).get('normalized_brand')}
        brands_to_create_names = set()

        for brand_name in all_brands_in_file:
            canonical_name = temp_translation_updates.get(brand_name, self.brand_translation_cache.get(brand_name, brand_name))
            if canonical_name not in self.caches['normalized_brand_names']:
                brands_to_create_names.add(canonical_name)
        
        # --- Step 2: Prepare ProductBrand Objects ---
        brands_to_bulk_create = [
            ProductBrand(name=name, normalized_name=name, name_variations=[name])
            for name in brands_to_create_names
        ]
        
        brands_to_bulk_update = []
        for brand_obj, variations in brands_to_update.items():
            if set(brand_obj.name_variations or []) != variations:
                brand_obj.name_variations = sorted(list(variations))
                brands_to_bulk_update.append(brand_obj)

        # --- Step 3: Database Operations for Brands ---
        with transaction.atomic():
            if brands_to_bulk_create:
                self.command.stdout.write(f"    - Creating {len(brands_to_bulk_create)} new brands.")
                ProductBrand.objects.bulk_create(brands_to_bulk_create, batch_size=500)
            
            if brands_to_bulk_update:
                self.command.stdout.write(f"    - Updating {len(brands_to_bulk_update)} existing brands.")
                ProductBrand.objects.bulk_update(brands_to_bulk_update, ['name_variations'], batch_size=500)

        # --- Step 4: Link Products to Brands ---
        # First, update the shared cache with any newly created brands
        if brands_to_bulk_create:
            newly_created_brands = ProductBrand.objects.filter(normalized_name__in=brands_to_create_names)
            for brand_obj in newly_created_brands:
                self.cache_updater('normalized_brand_names', brand_obj.normalized_name, brand_obj)
        
        products_to_link = []
        for product_data in processed_product_data_list:
            product_dict = product_data.get('product', {})
            normalized_brand = product_dict.get('normalized_brand')
            product_norm_string = product_dict.get('normalized_name_brand_size')

            if not normalized_brand or not product_norm_string:
                continue

            canonical_name = temp_translation_updates.get(normalized_brand, self.brand_translation_cache.get(normalized_brand, normalized_brand))
            brand_obj = self.caches['normalized_brand_names'].get(canonical_name)
            product_obj = self.caches['products_by_norm_string'].get(product_norm_string)

            if product_obj and brand_obj and product_obj.brand_id != brand_obj.id:
                product_obj.brand = brand_obj
                products_to_link.append(product_obj)
        
        if products_to_link:
            self.command.stdout.write(f"    - Linking {len(products_to_link)} products to their brands.")
            Product.objects.bulk_update(products_to_link, ['brand'], batch_size=500)

        # --- Step 5: Update Master Translation Cache (Final Step) ---
        if temp_translation_updates:
            self.command.stdout.write(f"    - Applying {len(temp_translation_updates)} updates to the master brand translation cache.")
            self.brand_translation_cache.update(temp_translation_updates)
            
        self.command.stdout.write("  - BrandManager: Finished processing brands.")
