from django.core.management.base import BaseCommand
from django.db import models # Import models for Count
from products.models import Price
from companies.models import Company, Store # Import Store

class Command(BaseCommand):
    help = 'Counts the total number of Price objects and provides a per-company and per-store breakdown.'

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
            self.stdout.write(f"{company.name}: {company_price_count:,}")

        self.stdout.write("\n--- Per-Store Breakdown (stores with prices) ---")
        # 3. Get the count per store (only for stores with prices)
        # Optimize by annotating stores with their price count
        stores_with_prices = Store.objects.annotate(
            price_count=models.Count('prices')
        ).filter(price_count__gt=0).order_by('company__name', 'store_name')

        for store in stores_with_prices:
            self.stdout.write(f"{store.company.name} - {store.store_name}: {store.price_count:,}")


        self.stdout.write(self.style.SUCCESS("\n--- Count Complete ---"))
