from django.core.management.base import BaseCommand
from products.models import Bargain, Price
from companies.models import StoreGroup

class Command(BaseCommand):
    help = 'Confirms that the set of stores with bargains is identical to the set of anchor stores with prices.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Confirming Anchor/Bargain Premise ---"))

        # --- Part 1: Find all unique stores that have bargain records ---
        self.stdout.write("\n[1] Finding all unique stores present in the Bargain table...")
        cheaper_store_ids = set(Bargain.objects.values_list('cheaper_store_id', flat=True).distinct())
        expensive_store_ids = set(Bargain.objects.values_list('expensive_store_id', flat=True).distinct())
        
        bargain_store_ids = cheaper_store_ids.union(expensive_store_ids)
        bargain_store_ids.discard(None) # Remove None if it exists
        
        self.stdout.write(f"    - Found {len(bargain_store_ids)} unique stores in the Bargain table.")
        
        # --- Part 2: Find all anchor stores that have price records ---
        self.stdout.write("\n[2] Finding all anchor stores that have Price records...")
        
        stores_with_prices = set(Price.objects.values_list('store_id', flat=True).distinct())
        self.stdout.write(f"    - Found {len(stores_with_prices)} unique stores with prices.")

        all_anchor_ids = set(StoreGroup.objects.filter(anchor__isnull=False).values_list('anchor_id', flat=True).distinct())
        self.stdout.write(f"    - Found {len(all_anchor_ids)} unique active anchor stores.")

        anchor_stores_with_prices = stores_with_prices.intersection(all_anchor_ids)
        self.stdout.write(f"    - Found {len(anchor_stores_with_prices)} stores that are BOTH anchors AND have prices.")

        # --- Part 3: Compare the two sets ---
        self.stdout.write("\n[3] Comparing the two sets of stores...")

        # Sort for consistent display
        sorted_bargain_stores = sorted(list(bargain_store_ids))
        sorted_anchor_stores = sorted(list(anchor_stores_with_prices))

        self.stdout.write(f"\nStores with Bargains ({len(sorted_bargain_stores)}):")
        self.stdout.write(str(sorted_bargain_stores))
        
        self.stdout.write(f"\nAnchor Stores with Prices ({len(sorted_anchor_stores)}):")
        self.stdout.write(str(sorted_anchor_stores))

        if sorted_bargain_stores == sorted_anchor_stores:
            self.stdout.write(self.style.SUCCESS("\n[CONCLUSION] The premise is correct. The two lists are identical."))
        else:
            self.stdout.write(self.style.ERROR("\n[CONCLUSION] The premise is incorrect. The lists are different."))
            
            # Show the differences
            in_bargains_not_anchors = bargain_store_ids - anchor_stores_with_prices
            in_anchors_not_bargains = anchor_stores_with_prices - bargain_store_ids

            if in_bargains_not_anchors:
                self.stdout.write(f"    - Stores in Bargain table but NOT in 'Anchors with Prices': {sorted(list(in_bargains_not_anchors))}")
            if in_anchors_not_bargains:
                self.stdout.write(f"    - Stores in 'Anchors with Prices' but NOT in Bargain table: {sorted(list(in_anchors_not_bargains))}")


        self.stdout.write("\n--- Command Complete ---")
