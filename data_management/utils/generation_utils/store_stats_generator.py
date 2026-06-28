from django.utils import timezone
from datetime import timedelta
from companies.models import Company, Store
from products.models import Price

class StoreStatsGenerator:
    """
    A utility to report on the health of store pricing data.
    """
    def __init__(self, command):
        self.command = command

    def run(self):
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        companies = Company.objects.order_by('name')

        self.command.stdout.write(self.command.style.SUCCESS("Store Pricing Data Health Report"))
        self.command.stdout.write(self.command.style.SUCCESS("="*40))

        for company in companies:
            total_stores_count = Store.objects.filter(company=company).count()

            self.command.stdout.write(f"\nCompany: {self.command.style.HTTP_INFO(company.name)}")

            if total_stores_count == 0:
                self.command.stdout.write("  - No stores found.")
                continue

            stores_with_prices_count = Price.objects.filter(
                store__company=company
            ).values('store_id').distinct().count()

            stores_with_fresh_prices_count = Price.objects.filter(
                store__company=company,
                scraped_date__gte=seven_days_ago
            ).values('store_id').distinct().count()

            self.command.stdout.write(f"  - Total Stores: {total_stores_count}")
            self.command.stdout.write(f"  - Stores with Price Data: {stores_with_prices_count}")
            self.command.stdout.write(f"  - Stores with Fresh Price Data (last 7 days): {stores_with_fresh_prices_count}")

        self.command.stdout.write(self.command.style.SUCCESS("\n" + "="*40))
        self.command.stdout.write(self.command.style.SUCCESS("Report Complete."))
