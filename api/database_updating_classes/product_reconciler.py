from products.models import Product, Price
from api.data.product_name_translation_table import PRODUCT_NAME_TRANSLATIONS
from datetime import datetime

class ProductReconciler:
    def __init__(self, command):
        self.command = command
        self.log_file = 'reconciliation_log.txt'
        self._initialize_log_file()

    def _initialize_log_file(self):
        # Write a header to the log file to indicate a new run
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n--- Reconciliation Run Started at {datetime.now().isoformat()} ---\n")

    def _log_merge(self, canonical, duplicate):
        # Log the details of the merge to the file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("----------------------------------------------------")
            f.write(f"Merging duplicate into canonical:\n")
            f.write(f"  [DUPLICATE] Name: {duplicate.name} | Brand: {duplicate.brand} | Size: {duplicate.size}\n")
            f.write(f"  [CANONICAL] Name: {canonical.name} | Brand: {canonical.brand} | Size: {canonical.size}\n")
            f.write("----------------------------------------------------\n")

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run started."))
        
        if not PRODUCT_NAME_TRANSLATIONS:
            self.command.stdout.write("Translation table is empty. Nothing to reconcile.")
            return

        variation_strings = list(PRODUCT_NAME_TRANSLATIONS.keys())
        potential_duplicates = Product.objects.filter(normalized_name_brand_size__in=variation_strings)

        if not potential_duplicates:
            self.command.stdout.write("No products found matching any variation strings.")
            return

        self.command.stdout.write(f"Found {len(potential_duplicates)} potential duplicate products to process.")

        for duplicate_product in potential_duplicates:
            # Find the canonical string from the table
            canonical_string = PRODUCT_NAME_TRANSLATIONS.get(duplicate_product.normalized_name_brand_size)
            if not canonical_string:
                continue

            try:
                # Use .get() which is safe because normalized_name_brand_size is unique
                canonical_product = Product.objects.get(normalized_name_brand_size=canonical_string)
                
                if canonical_product.id == duplicate_product.id:
                    continue

                self._merge_products(canonical_product, duplicate_product)

            except Product.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Could not find canonical product for {canonical_string}. Skipping."))
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred for {duplicate_product.normalized_name_brand_size}: {e}"))
                continue

        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run finished."))

    def _merge_products(self, canonical, duplicate):
        """
        Merges the duplicate product into the canonical product.
        """
        # Log the action before doing anything else
        self._log_merge(canonical, duplicate)

        self.command.stdout.write(f"  - Merging '{duplicate.name}' into '{canonical.name}'")
        
        # --- Enrich Fields ---
        updated = False
        fields_to_check = ['url', 'image_url', 'country_of_origin', 'ingredients']
        for field_name in fields_to_check:
            if not getattr(canonical, field_name) and getattr(duplicate, field_name):
                setattr(canonical, field_name, getattr(duplicate, field_name))
                updated = True

        # Handle description (prefer shorter)
        if duplicate.description:
            if not canonical.description or len(duplicate.description) < len(canonical.description):
                canonical.description = duplicate.description
                updated = True

        # Handle name variations
        if duplicate.name_variations:
            if not canonical.name_variations:
                canonical.name_variations = []
            for variation in duplicate.name_variations:
                if variation not in canonical.name_variations:
                    canonical.name_variations.append(variation)
                    updated = True
        
        if updated:
            canonical.save()

        # --- De-duplicate and Move Prices ---
        canonical_price_keys = set(
            (p.store_id, p.scraped_at.date()) for p in Price.objects.filter(product=canonical)
        )
        prices_to_move = Price.objects.filter(product=duplicate)
        moved_count = 0
        deleted_count = 0

        for price in prices_to_move:
            price_key = (price.store_id, price.scraped_at.date())
            if price_key not in canonical_price_keys:
                price.product = canonical
                price.save()
                moved_count += 1
            else:
                price.delete()
                deleted_count += 1

        self.command.stdout.write(f"    - Moved {moved_count} prices and deleted {deleted_count} duplicate prices.")

        # --- Delete Duplicate Product ---
        duplicate.delete()
        self.command.stdout.write(f"    - Deleted duplicate product.")
