from products.models import ProductBrand

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
        Ensures all brands from the raw data exist in the database
        and updates the shared cache.
        """
        self.command.stdout.write("  - BrandManager: Processing brands...")
        
        new_brand_names_to_create = set()
        
        # 1. Identify new brands from raw data
        for product_data in raw_product_data:
            normalized_brand = product_data.get('product', {}).get('normalized_brand')
            if normalized_brand and normalized_brand not in self.caches['normalized_brand_names']:
                new_brand_names_to_create.add(normalized_brand)

        if not new_brand_names_to_create:
            self.command.stdout.write("    - No new brands to create.")
            return

        self.command.stdout.write(f"    - Found {len(new_brand_names_to_create)} new brands to create.")

        # 2. Prepare for bulk creation
        brand_objects_to_create = []
        for normalized_name in new_brand_names_to_create:
            # For now, use normalized_name as the canonical name
            brand_objects_to_create.append(
                ProductBrand(name=normalized_name, normalized_name=normalized_name)
            )

        # 3. Perform bulk create
        try:
            from django.db import transaction # Import here to avoid circular dependency if ProductBrand imports BrandManager
            with transaction.atomic():
                ProductBrand.objects.bulk_create(brand_objects_to_create, batch_size=500)
            self.command.stdout.write(self.command.style.SUCCESS(f"    - Successfully created {len(brand_objects_to_create)} new brands."))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error creating brands: {e}"))
            raise # Re-raise to stop processing if brand creation fails

        # 4. Update the shared cache
        # Re-fetch to get PKs
        newly_created_brands = ProductBrand.objects.filter(normalized_name__in=new_brand_names_to_create)
        for brand_obj in newly_created_brands:
            self.cache_updater('normalized_brand_names', brand_obj.normalized_name, brand_obj)
        self.command.stdout.write("    - Shared brand cache updated.")
