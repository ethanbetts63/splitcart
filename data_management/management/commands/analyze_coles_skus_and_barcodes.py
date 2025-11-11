from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Store, Company
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Analyzes Coles stores for product SKU and barcode presence.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles SKU and Barcode Analysis ---"))

        try:
            coles_company = Company.objects.get(name__iexact='coles')
            all_coles_stores = Store.objects.filter(company=coles_company)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR("Could not find 'Coles' company in the database."))
            return

        for store in all_coles_stores:
            # Find product IDs associated with the current store through the Price model
            product_ids = Price.objects.filter(store=store).values_list('product_id', flat=True).distinct()
            store_products = Product.objects.filter(pk__in=product_ids)
            total_store_products = store_products.count()

            if total_store_products == 0:
                continue # Skip stores with no products 

            products_with_coles_sku = store_products.filter(company_skus__has_key='coles')
            count_with_coles_sku = products_with_coles_sku.count()

            products_with_barcode = store_products.filter(barcode__isnull=False).exclude(barcode__exact='')
            count_with_barcode = products_with_barcode.count()

            products_with_both = store_products.filter(
                company_skus__has_key='coles',
                barcode__isnull=False
            ).exclude(barcode__exact='')
            count_with_both = products_with_both.count()

            self.stdout.write(f"\n--- Analyzing Store: {store.store_name} ({store.store_id}) ---")
            self.stdout.write(f"Total Products for this store: {total_store_products}")
            self.stdout.write(f"  - Products with Coles SKU: {count_with_coles_sku}")
            self.stdout.write(f"  - Products with Barcode:   {count_with_barcode}")
            self.stdout.write(f"  - Products with Both (SKU & Barcode): {count_with_both}")
            self.stdout.write("-" * 30)

        self.stdout.write(self.style.SUCCESS("\n--- Coles SKU and Barcode Analysis Complete ---"))
