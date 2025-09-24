from products.models import ProductBrand
from data_management.utils.product_normalizer import ProductNormalizer

class BrandManager:
    """
    Manages the creation of and updates to ProductBrand objects during a database update.
    It uses a cache to be efficient and handles the logic for consolidating brand name variations.
    """
    def __init__(self, command):
        self.command = command
        # In-memory cache to hold brand objects for the duration of a file-processing run.
        # Format: {normalized_name: brand_obj}
        self.brand_cache = {}
        # A set of brand objects whose name_variations list has been modified.
        self.brands_to_update = set()

    def process_brand(self, brand_name: str, normalized_brand_name: str, company_name: str):
        """
        Processes a single brand from a product record. It uses a cache to avoid
        repeated database queries for the same brand within a single file.
        It finds or creates the canonical brand based on the normalized name and
        queues up any new name variations to be saved later.
        """
        if not brand_name or not normalized_brand_name:
            return

        # Check the local cache first to minimize DB hits.
        if normalized_brand_name in self.brand_cache:
            brand = self.brand_cache[normalized_brand_name]
        else:
            # If not in cache, get or create the brand from the database.
            # The normalized_name is the unique key.
            brand, created = ProductBrand.objects.get_or_create(
                normalized_name=normalized_brand_name,
                defaults={'name': brand_name}
            )
            self.brand_cache[normalized_brand_name] = brand

        # Check if the raw brand name is a new variation.
        if brand_name != brand.name and brand_name not in brand.name_variations:
            brand.name_variations.append(brand_name)
            # Also update the normalized variations for searching.
            normalized_variation = ProductNormalizer._get_normalized_brand_name(brand_name)
            if normalized_variation not in brand.normalized_name_variations:
                brand.normalized_name_variations.append(normalized_variation)
            self.brands_to_update.add(brand)



    def commit(self):
        """
        Commits all pending changes to the database.
        Specifically, it saves all new name variations that have been collected.
        """
        if not self.brands_to_update:
            self.command.stdout.write("  - No brand variations to update.")
            return
            
        # Use bulk_update to save all changes to both variation fields in one query.
        ProductBrand.objects.bulk_update(self.brands_to_update, ['name_variations', 'normalized_name_variations'])
        self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully updated {len(self.brands_to_update)} brands with new name variations."))
        
        # Clear the set for the next file run.
        self.brands_to_update.clear()
