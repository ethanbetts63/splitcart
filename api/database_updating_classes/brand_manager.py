from products.models import ProductBrand

class BrandManager:
    """
    Manages the creation of new ProductBrand objects during a database update.
    It ensures that only genuinely new brands are created, avoiding duplicates.
    """
    def __init__(self, command):
        self.command = command
        self.new_brands_cache = set()
        self.brands_to_create = []
        self._build_cache()

    def _build_cache(self):
        """
        Builds an in-memory cache of all existing brand names for fast lookups.
        """
        self.command.stdout.write("--- Building BrandManager cache ---")
        self.existing_brands_cache = set(ProductBrand.objects.values_list('name', flat=True))
        self.command.stdout.write(f"  - Cached {len(self.existing_brands_cache)} existing brands.")

    def process_brand(self, brand_name: str):
        """
        Processes a brand name from a product. If the brand is new, it's
        queued for creation.
        """
        if not brand_name:
            return

        if brand_name in self.existing_brands_cache:
            return
        
        if brand_name in self.new_brands_cache:
            return

        self.command.stdout.write(f"  - Discovered new brand for creation: '{brand_name}'")
        new_brand = ProductBrand(name=brand_name)
        self.brands_to_create.append(new_brand)
        self.new_brands_cache.add(brand_name)
        self.existing_brands_cache.add(brand_name)

    def commit(self):
        """
        Commits all the new brands to the database in a single batch.
        """
        if not self.brands_to_create:
            self.command.stdout.write("  - No new brands to create.")
            return

        self.command.stdout.write(f"  - Committing {len(self.brands_to_create)} new brands to the database...")
        
        created_count = 0
        for brand in self.brands_to_create:
            try:
                brand.save()
                created_count += 1
            except Exception as e:
                self.command.stderr.write(self.style.ERROR(f"Could not save brand '{brand.name}': {e}"))

        self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully created {created_count} new brands."))
