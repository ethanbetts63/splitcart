from django.core.management.base import BaseCommand
from api.analysers.store_grouping import group_stores_by_price_correlation

class Command(BaseCommand):
    help = 'Groups stores by price correlation.'

    def add_arguments(self, parser):
        parser.add_argument('--company-name', type=str, required=True, help='The name of the company to group stores for.')
        parser.add_argument('--threshold', type=float, default=99.5, help='The correlation threshold for grouping stores.')

    def handle(self, *args, **options):
        company_name = options['company_name']
        threshold = options['threshold']

        self.stdout.write(self.style.SUCCESS(f"Grouping stores for '{company_name}' with a threshold of {threshold}%"))
        
        groups, island_stores = group_stores_by_price_correlation(company_name, threshold)

        if groups:
            self.stdout.write(self.style.SUCCESS("\n--- Store Groups ---"))
            for i, group in enumerate(groups):
                self.stdout.write(self.style.SUCCESS(f"\nGroup {i + 1}:"))
                for store in group:
                    self.stdout.write(f"  - {store.store_name} ({store.store_id})")
        
        if island_stores:
            self.stdout.write(self.style.WARNING("\n--- Island Stores (no strong correlation found) ---"))
            for store in island_stores:
                self.stdout.write(f"  - {store.store_name} ({store.store_id})")
        
        if not groups and not island_stores:
            self.stdout.write(self.style.WARNING("No stores found for this company."))
