from django.core.management.base import BaseCommand
from products.models import Bargain
from companies.models import Store

class Command(BaseCommand):
    help = 'Lists all unique stores that participate in any bargain, grouped by company.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Finding all stores with bargains ---"))

        # Get unique store IDs from both cheaper and expensive sides of bargains
        cheaper_store_ids = set(Bargain.objects.values_list('cheaper_store_id', flat=True).distinct())
        self.stdout.write(f"Found {len(cheaper_store_ids)} unique 'cheaper' stores.")

        expensive_store_ids = set(Bargain.objects.values_list('expensive_store_id', flat=True).distinct())
        self.stdout.write(f"Found {len(expensive_store_ids)} unique 'expensive' stores.")

        # The distinct() call on the values_list query already handles uniqueness, 
        # but the set union is a robust way to combine them.
        all_bargain_store_ids = cheaper_store_ids.union(expensive_store_ids)
        
        # Filter out None if it exists in the set, which can happen if the columns are not populated.
        all_bargain_store_ids.discard(None)

        self.stdout.write(f"Found a total of {len(all_bargain_store_ids)} unique stores participating in bargains.")

        if not all_bargain_store_ids:
            self.stdout.write(self.style.WARNING("No stores found in the bargain table. The 'cheaper_store_id' and 'expensive_store_id' columns may be empty."))
            return

        # Fetch store details to make the output more readable
        stores = Store.objects.filter(id__in=all_bargain_store_ids).select_related('company').order_by('company__name', 'id')
        
        self.stdout.write("\n--- List of Stores with Bargains ---")
        
        # Group by company for readability
        stores_by_company = {}
        for store in stores:
            company_name = store.company.name
            if company_name not in stores_by_company:
                stores_by_company[company_name] = []
            stores_by_company[company_name].append(store.id)

        for company, store_ids in stores_by_company.items():
            self.stdout.write(f"\n{self.style.SUCCESS(company)}:")
            # To avoid overly long lines, print in chunks or just limit the display
            if len(store_ids) > 50:
                 self.stdout.write(f"  Store IDs: {store_ids[:50]} ... (and {len(store_ids) - 50} more)")
            else:
                 self.stdout.write(f"  Store IDs: {store_ids}")

        self.stdout.write("\n--- Command Complete ---")
