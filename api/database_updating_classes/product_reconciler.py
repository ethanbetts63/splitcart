from products.models import Product, Price

class ProductReconciler:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run started."))
        # Main logic for finding duplicates will be added here later.
        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run finished."))

    def _merge_products(self, canonical, duplicate):
        """
        Merges the duplicate product into the canonical product.
        """
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
