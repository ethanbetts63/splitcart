from django.core.management.base import BaseCommand
from companies.models import Company, Store
from django.db.models import Count

class Command(BaseCommand):
    help = 'Lists all Coles stores and the number of products in each.'

    def handle(self, *args, **options):
        self.stdout.write("Fetching Coles stores and their product counts...")

        try:
            coles_company = Company.objects.get(name__iexact='Coles')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR("Company 'Coles' not found."))
            return

        stores = Store.objects.filter(company=coles_company).exclude(store_name__icontains='Liquorland').exclude(store_name__icontains='Vintage Cellars').annotate(price_count=Count('prices')).order_by('-price_count')

        if not stores.exists():
            self.stdout.write(self.style.WARNING("No stores found for Coles."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {stores.count()} stores for Coles:"))
        self.stdout.write("-" * 50)
        self.stdout.write(f"{'Store Name':<30} | {'Store ID':<10} | {'Product Count':<15}")
        self.stdout.write("-" * 50)

        for store in stores:
            self.stdout.write(f"{store.store_name:<30} | {store.id:<10} | {store.price_count:<15}")

        self.stdout.write("-" * 50)
