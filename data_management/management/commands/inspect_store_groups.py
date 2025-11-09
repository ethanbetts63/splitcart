from django.core.management.base import BaseCommand
from companies.models import Company

class Command(BaseCommand):
    help = 'Inspects the state of store groups by reporting store and store group counts for each company.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Store Group Inspection ---"))

        companies = Company.objects.all().prefetch_related('stores', 'store_groups')

        if not companies:
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in companies:
            store_count = company.stores.count()
            stores_with_prices_count = company.stores.filter(prices__isnull=False).distinct().count()
            group_count = company.store_groups.count()
            groups_with_priced_anchor_count = company.store_groups.filter(anchor__prices__isnull=False).distinct().count()

            self.stdout.write(f"\nCompany: {company.name}")
            self.stdout.write(f"  - Total Stores: {store_count}")
            self.stdout.write(f"  - Stores with Prices: {stores_with_prices_count}")
            self.stdout.write(f"  - Total Store Groups: {group_count}")
            self.stdout.write(f"  - Groups with Priced Anchor: {groups_with_priced_anchor_count}")

            if store_count == group_count and store_count > 0:
                self.stdout.write(self.style.WARNING("  - Observation: The number of stores equals the number of groups. No grouping has occurred."))
            elif group_count > 0:
                self.stdout.write(self.style.SUCCESS(f"  - Observation: Grouping has occurred. {groups_with_priced_anchor_count} groups are usable for comparison."))
            else:
                self.stdout.write("  - Observation: No stores or groups to compare.")
        
        self.stdout.write(self.style.SUCCESS("\n--- Inspection Complete ---"))
