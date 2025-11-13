from django.core.management.base import BaseCommand
from collections import defaultdict
from companies.models import Company
from products.models import Product, Price, SKU

class Command(BaseCommand):
    help = 'Analyzes SKU duplication within each company.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting SKU Duplication Analysis ---"))

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in companies:
            company_name_lower = company.name.lower()
            self.stdout.write(self.style.HTTP_INFO(f"\nAnalyzing company: {company.name}"))

            # 1. Get all unique product PKs associated with this company
            product_pks = Price.objects.filter(store__company=company).values_list('product_id', flat=True).distinct()
            total_company_products = len(product_pks)

            if total_company_products == 0:
                self.stdout.write(self.style.WARNING(f"  No products found for {company.name}. Skipping."))
                continue

            # 2. Build the SKU-to-Product map
            sku_to_products = defaultdict(list)
            # Query SKU objects directly for the given company and product PKs
            skus_for_company_products = SKU.objects.select_related('product').filter(
                company=company,
                product_id__in=product_pks
            )
            for sku_obj in skus_for_company_products:
                sku_to_products[sku_obj.sku].append(sku_obj.product.pk)

            # 3. Analyze the map for conflicts
            conflicting_skus = {}
            conflicting_product_pks = set()
            
            for sku, pks in sku_to_products.items():
                if len(pks) > 1:
                    # We have a conflict: one SKU maps to multiple products
                    conflicting_skus[sku] = pks
                    conflicting_product_pks.update(pks)

            # 4. Calculate metrics
            total_conflicting_products = len(conflicting_product_pks)
            
            # The number of products after deduplication would be:
            # (Total products) - (all products involved in conflicts) + (the number of unique conflicting SKUs)
            # This represents replacing the group of conflicting products with a single product for each conflict.
            products_after_deduplication = total_company_products - total_conflicting_products + len(conflicting_skus)

            # 5. Print results
            self.stdout.write(f"  - Total products sold: {total_company_products}")
            self.stdout.write(self.style.WARNING(f"  - Products with a conflicting SKU: {total_conflicting_products}") + f" (across {len(conflicting_skus)} unique SKUs).")
            self.stdout.write(self.style.SUCCESS(f"  - Estimated products after SKU-based deduplication: {products_after_deduplication}"))
            
            # Optionally, print some examples of conflicts
            if conflicting_skus:
                self.stdout.write("  - Example conflicts (SKU -> Product PKs):")
                count = 0
                for sku, pks in conflicting_skus.items():
                    if count >= 5:
                        self.stdout.write("    ...")
                        break
                    self.stdout.write(f"    - {sku}: {pks}")
                    count += 1

        self.stdout.write(self.style.SUCCESS("\n--- SKU Duplication Analysis Complete ---"))
