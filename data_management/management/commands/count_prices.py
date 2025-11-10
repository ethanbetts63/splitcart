from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Price
from companies.models import Company, Store, StoreGroup

class Command(BaseCommand):
    help = 'Counts the total number of Price objects and provides a per-company and per-group breakdown.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Counting Price Objects ---"))

        # 1. Get the total count of prices
        total_prices = Price.objects.count()
        self.stdout.write(f"Total prices in the system: {total_prices:,}")

        self.stdout.write("\n--- Per-Company Breakdown ---")
        # 2. Get the count per company efficiently with a single query
        company_price_counts = Price.objects.values('store__company__name').annotate(
            count=Count('id')
        ).order_by('store__company__name')

        for item in company_price_counts:
            company_name = item['store__company__name']
            count = item['count']
            if company_name and count > 0:
                self.stdout.write(f"{company_name}: {count:,}")

        self.stdout.write("\n" + self.style.SUCCESS("--- Per-Group Breakdown ---"))
        
        # Pre-fetch all price counts in a single query for efficiency
        price_counts_by_store_id = {
            item['store_id']: item['count'] 
            for item in Price.objects.values('store_id').annotate(count=Count('id'))
        }

        # Get IDs of stores that have at least one price
        stores_with_prices_ids = price_counts_by_store_id.keys()

        # Get all store groups where the anchor has prices, prefetching related data
        store_groups = StoreGroup.objects.filter(
            anchor_id__in=stores_with_prices_ids
        ).prefetch_related('memberships__store', 'company', 'anchor').order_by('company__name', 'id')

        for group in store_groups:
            self.stdout.write(self.style.SUCCESS(f"\nGroup: {group}"))
            
            non_anchor_price_count = 0
            
            # Process the anchor store first
            if group.anchor:
                self.stdout.write(self.style.WARNING("  Anchor Store:"))
                count = price_counts_by_store_id.get(group.anchor.id, 0)
                self.stdout.write(f"    - {group.anchor.store_name}: {count:,}")
            else:
                self.stdout.write(self.style.WARNING("  No anchor store set for this group."))

            # Process non-anchor stores by iterating through memberships
            for membership in group.memberships.all():
                store = membership.store
                # Exclude the anchor from this calculation, as it's handled above
                if group.anchor and store.id == group.anchor.id:
                    continue
                non_anchor_price_count += price_counts_by_store_id.get(store.id, 0)
            
            self.stdout.write(self.style.WARNING("  Non-Anchor Stores Total:"))
            self.stdout.write(f"    - Total prices: {non_anchor_price_count:,}")

        self.stdout.write(self.style.SUCCESS("\n--- Count Complete ---"))
