from products.models import ProductBrand
from django.db import transaction

class BrandManager:
    """
    Manages the creation and updating of ProductBrand objects.
    """
    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

    def process(self, raw_product_data):
        """
        Ensures all brands from the raw data exist in the database,
        updates existing brands with new name variations, and updates the shared cache.
        """
        self.command.stdout.write("  - BrandManager: Processing brands...")
        
        new_brand_names_to_create = set()
        brands_to_update = {}  # Using dict to store {brand_obj: set_of_variations}

        # 1. Identify new brands and new variations for existing brands
        for product_data in raw_product_data:
            product_dict = product_data.get('product', {})
            normalized_brand = product_dict.get('normalized_brand')
            raw_brand = product_dict.get('brand')

            if not normalized_brand:
                continue

            if normalized_brand in self.caches['normalized_brand_names']:
                # It's an existing brand, check for new variations
                brand_obj = self.caches['normalized_brand_names'][normalized_brand]
                
                # Initialize variations set if not already in our update dict
                if brand_obj not in brands_to_update:
                    # Ensure name_variations is a list, default to empty list if None
                    brands_to_update[brand_obj] = set(brand_obj.name_variations or [])

                # Add the raw brand name as a potential variation
                if raw_brand:
                    brands_to_update[brand_obj].add(raw_brand)
                # Also add the normalized brand name as a variation
                brands_to_update[brand_obj].add(brand_obj.name)

            else:
                # It's a new brand
                new_brand_names_to_create.add(normalized_brand)

        # 2. Prepare and perform bulk update for existing brands
        updated_brand_objects = []
        for brand_obj, variations_set in brands_to_update.items():
            # Only update if the variations have actually changed
            current_variations = set(brand_obj.name_variations or [])
            if variations_set != current_variations:
                brand_obj.name_variations = sorted(list(variations_set))
                updated_brand_objects.append(brand_obj)

        if updated_brand_objects:
            self.command.stdout.write(f"    - Found {len(updated_brand_objects)} brands to update with new variations.")
            try:
                with transaction.atomic():
                    ProductBrand.objects.bulk_update(updated_brand_objects, ['name_variations'], batch_size=500)
                self.command.stdout.write(self.command.style.SUCCESS(f"    - Successfully updated {len(updated_brand_objects)} brands."))
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"    - Error updating brand variations: {e}"))
                raise
        else:
            self.command.stdout.write("    - No existing brands needed updates.")

        # 3. Prepare and perform bulk create for new brands
        if not new_brand_names_to_create:
            self.command.stdout.write("    - No new brands to create.")
            return

        self.command.stdout.write(f"    - Found {len(new_brand_names_to_create)} new brands to create.")
        brand_objects_to_create = [
            ProductBrand(name=normalized_name, normalized_name=normalized_name)
            for normalized_name in new_brand_names_to_create
        ]

        try:
            with transaction.atomic():
                ProductBrand.objects.bulk_create(brand_objects_to_create, batch_size=500)
            self.command.stdout.write(self.command.style.SUCCESS(f"    - Successfully created {len(brand_objects_to_create)} new brands."))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error creating brands: {e}"))
            raise

        # 4. Update the shared cache with newly created brands
        newly_created_brands = ProductBrand.objects.filter(normalized_name__in=new_brand_names_to_create)
        for brand_obj in newly_created_brands:
            self.cache_updater('normalized_brand_names', brand_obj.normalized_name, brand_obj)
        self.command.stdout.write("    - Shared brand cache updated with new brands.")
