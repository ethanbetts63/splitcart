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
        # 2. Get the count per company
        companies = Company.objects.all().order_by('name')
        for company in companies:
            company_price_count = Price.objects.filter(store__company=company).count()
            if company_price_count > 0:
                self.stdout.write(f"{company.name}: {company_price_count:,}")

        self.stdout.write("\n" + self.style.SUCCESS("--- Per-Group Breakdown ---"))
        
        # Pre-fetch all price counts in a single query for efficiency
        price_counts_by_store_id = {
            item['store_id']: item['count'] 
            for item in Price.objects.values('store_id').annotate(count=Count('id'))
        }

        # Get all store groups, prefetching the related stores
        store_groups = StoreGroup.objects.prefetch_related('stores').all().order_by('name')

        for group in store_groups:
            self.stdout.write(self.style.SUCCESS(f"\nGroup: {group.name} (ID: {group.id})"))
            
            non_anchor_price_count = 0
            anchor_stores = []
            non_anchor_stores = []

            # Separate stores into anchor and non-anchor
            for store in group.stores.all():
                if store.is_anchor:
                    anchor_stores.append(store)
                else:
                    non_anchor_stores.append(store)

            # Process anchor stores
            if anchor_stores:
                self.stdout.write(self.style.WARNING("  Anchor Stores:"))
                for anchor in anchor_stores:
                    count = price_counts_by_store_id.get(anchor.id, 0)
                    self.stdout.write(f"    - {anchor.store_name}: {count:,}")
            else:
                self.stdout.write(self.style.WARNING("  No anchor stores found for this group."))

            # Process non-anchor stores
            for non_anchor in non_anchor_stores:
                non_anchor_price_count += price_counts_by_store_id.get(non_anchor.id, 0)
            
            self.stdout.write(self.style.WARNING("  Non-Anchor Stores Total:"))
            self.stdout.write(f"    - Total prices: {non_anchor_price_count:,}")

        self.stdout.write(self.style.SUCCESS("\n--- Count Complete ---"))
