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
        Builds an in-memory cache of all existing normalized brand names for fast lookups.
        """
        self.command.stdout.write("--- Building BrandManager cache ---")
        self.existing_brands_cache = set(ProductBrand.objects.values_list('normalized_name', flat=True))
        self.command.stdout.write(f"  - Cached {len(self.existing_brands_cache)} existing brands.")

    def process_brand(self, brand_name: str, normalized_brand_name: str):
        """
        Processes a brand name from a product. If the brand is new (based on its
        normalized name), it's queued for creation using its original name.
        """
        if not brand_name or not normalized_brand_name:
            return

        # Check against cache of normalized names
        if normalized_brand_name in self.existing_brands_cache:
            return
        
        if normalized_brand_name in self.new_brands_cache:
            return

        # If we get here, it's a genuinely new brand.
        self.command.stdout.write(f"  - Discovered new brand for creation: '{brand_name}' (Normalized: '{normalized_brand_name}')")
        # Create the object with the original, prettier name.
        # The model's save() method will handle creating the normalized_name field.
        new_brand = ProductBrand(name=brand_name)
        self.brands_to_create.append(new_brand)
        self.new_brands_cache.add(normalized_brand_name)
        self.existing_brands_cache.add(normalized_brand_name)

    def commit(self):
        """
        Commits all the new brands to the database in a single batch.
        """
        if not self.brands_to_create:
            self.command.stdout.write("  - No new brands to create.")
            return
        
        created_count = 0
        for brand in self.brands_to_create:
            try:
                brand.save()
                created_count += 1
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Could not save brand '{brand.name}': {e}"))

        self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully created {created_count} new brands."))
