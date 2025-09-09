from products.models import ProductBrand

class BrandManager:
    """
    Manages the creation of new ProductBrand objects during a database update.
    It collects all brands from a file, de-duplicates them, and creates new ones
    in a single, efficient batch.
    """
    def __init__(self, command):
        self.command = command
        # Use a dict to store the original name, de-duplicating by normalized name.
        # Format: {normalized_name: original_name}
        self.processed_brands = {}

    def process_brand(self, brand_name: str, normalized_brand_name: str):
        """
        Collects a brand from a product, preparing it for batch creation.
        The first-seen original name for a given normalized name is preserved.
        """
        if not brand_name or not normalized_brand_name:
            return
        
        # If we see a normalized name again, we don't overwrite it.
        # This keeps the first-seen original name as the canonical one for this batch.
        if normalized_brand_name not in self.processed_brands:
            self.processed_brands[normalized_brand_name] = brand_name

    def commit(self):
        """
        Finds all genuinely new brands from the ones collected and commits them
        to the database in a single, efficient bulk_create operation.
        """
        if not self.processed_brands:
            self.command.stdout.write("  - No brand information to process.")
            return

        all_normalized_names = self.processed_brands.keys()

        # Find which brands from this batch already exist in the DB
        existing_brands = set(
            ProductBrand.objects.filter(
                normalized_name__in=all_normalized_names
            ).values_list('normalized_name', flat=True)
        )

        # Determine which brands are truly new by set difference
        new_normalized_names = all_normalized_names - existing_brands

        if not new_normalized_names:
            self.command.stdout.write("  - All processed brands already exist in the database.")
            return

        # Create new ProductBrand objects for the new names, ensuring the original name is unique within this batch
        brands_to_create = []
        names_in_batch = set()
        for normalized_name in new_normalized_names:
            original_name = self.processed_brands[normalized_name]
            if original_name not in names_in_batch:
                brands_to_create.append(ProductBrand(name=original_name, normalized_name=normalized_name))
                names_in_batch.add(original_name)

        if not brands_to_create:
            self.command.stdout.write("  - All new brands were duplicates within the same batch. Nothing to create.")
            return

        try:
            # Create all new brands in a single database call
            ProductBrand.objects.bulk_create(brands_to_create)
            self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully created {len(brands_to_create)} new brands."))
        except Exception as e:
            # This might catch errors during the model's clean() method if bulk_create is complex
            self.command.stderr.write(self.command.style.ERROR(f"Could not bulk create brands: {e}"))