from django.core.management.base import BaseCommand
from companies.models import Company
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Analyzes the consistency and coverage of SKUs for each company.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting SKU Consistency Analysis ---"))

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in companies:
            self.stdout.write(self.style.HTTP_INFO(f"\nAnalyzing company: {company.name}"))

            # 1. Get all unique product PKs associated with this company via prices
            product_pks = Price.objects.filter(store__company=company).values_list('product_id', flat=True).distinct()
            total_company_products = len(product_pks)

            if total_company_products == 0:
                self.stdout.write(self.style.WARNING(f"  No products found for {company.name}. Skipping."))
                continue

            self.stdout.write(f"  Found {total_company_products} unique products sold by {company.name}.")

            # 2. Get all relevant Product objects in one query
            products = Product.objects.filter(pk__in=product_pks)

            # 3. Initialize counters
            products_with_any_sku = 0
            products_with_multiple_skus = 0

            # 4. Analyze the products
            for product in products:
                # The company_skus field might not have an entry for this company
                sku_list = product.company_skus.get(company.name.lower(), [])
                
                if len(sku_list) > 0:
                    products_with_any_sku += 1
                
                if len(sku_list) > 1:
                    products_with_multiple_skus += 1

            # 5. Calculate and print percentages
            if total_company_products > 0:
                percent_with_any_sku = (products_with_any_sku / total_company_products) * 100
                percent_with_multiple_skus = (products_with_multiple_skus / total_company_products) * 100
            else:
                percent_with_any_sku = 0
                percent_with_multiple_skus = 0

            self.stdout.write(self.style.SUCCESS(f"  - SKU Coverage: {percent_with_any_sku:.2f}%") + f" ({products_with_any_sku} of {total_company_products} products have at least one SKU).")
            self.stdout.write(self.style.SUCCESS(f"  - SKU Instability: {percent_with_multiple_skus:.2f}%") + f" ({products_with_multiple_skus} of {total_company_products} products have more than one SKU).")

        self.stdout.write(self.style.SUCCESS("\n--- SKU Analysis Complete ---"))
