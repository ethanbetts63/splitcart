from django.core.management.base import BaseCommand
from collections import defaultdict
from companies.models import Company
from products.models import Product, Price, SKU

class Command(BaseCommand):
    help = 'Analyzes conflicting SKUs to see how many of the associated products have barcodes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Conflicting SKU Barcode Analysis ---"))

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in companies:
            company_name_lower = company.name.lower()
            self.stdout.write(self.style.HTTP_INFO(f"\nAnalyzing company: {company.name}"))

            # 1. Get all unique product PKs associated with this company
            product_pks = Price.objects.filter(store__company=company).values_list('product_id', flat=True).distinct()
            if not product_pks:
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
                sku_to_products[sku_obj.sku].append(sku_obj.product)

            # 3. Find and analyze conflicting SKUs
            conflicting_skus = {sku: prods for sku, prods in sku_to_products.items() if len(prods) > 1}
            
            if not conflicting_skus:
                self.stdout.write(self.style.SUCCESS("  No conflicting SKUs found for this company."))
                continue

            total_conflicts = len(conflicting_skus)
            proven_conflicts = 0  # Conflicts with multiple, distinct barcodes
            
            self.stdout.write(f"  Found {total_conflicts} SKUs that map to multiple products.")

            # 4. Analyze the barcodes within each conflict
            for sku, conflicting_products in conflicting_skus.items():
                # Collect all non-null, non-empty barcodes for this group of products
                barcodes_found = {p.barcode for p in conflicting_products if p.barcode}
                
                # A "proven conflict" is one where we have at least two different, valid barcodes
                if len(barcodes_found) > 1:
                    proven_conflicts += 1

            # 5. Print results
            if total_conflicts > 0:
                proven_conflict_percentage = (proven_conflicts / total_conflicts) * 100
            else:
                proven_conflict_percentage = 0

            self.stdout.write(self.style.WARNING(f"  - Proven Conflicts: {proven_conflicts} of {total_conflicts} conflicting SKUs are proven to be incorrect.") + f" ({proven_conflict_percentage:.2f}%)")
            self.stdout.write("    (A 'proven conflict' means the same SKU maps to products with different, valid barcodes).")

        self.stdout.write(self.style.SUCCESS("\n--- Conflicting SKU Barcode Analysis Complete ---"))
