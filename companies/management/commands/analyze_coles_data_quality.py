from django.core.management.base import BaseCommand
from companies.models import Company, Store
from products.models import Product, Price
from django.db.models import Q, Count

class Command(BaseCommand):
    help = 'Analyzes data quality for all Coles stores regarding barcodes and SKUs.'

    def handle(self, *args, **options):
        try:
            coles_company = Company.objects.get(name__iexact='Coles')
        except Company.DoesNotExist:
            self.stderr.write(self.style.ERROR("Company 'Coles' not found in the database."))
            return

        stores = Store.objects.filter(company=coles_company)
        if not stores.exists():
            self.stdout.write(self.style.WARNING("No Coles stores found in the database."))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Analyzing Data Quality for {stores.count()} Coles Stores ---"))

        # Overall counters
        overall_total_products = 0
        overall_has_barcode = 0
        overall_has_sku = 0
        overall_has_both = 0

        for store in stores:
            self.stdout.write(f"\n--- Store: {store.store_name} (PK: {store.pk}) ---")
            
            product_ids = Price.objects.filter(store=store).values_list('product_id', flat=True).distinct()
            products = Product.objects.filter(id__in=product_ids)
            
            total_products = products.count()
            if total_products == 0:
                self.stdout.write("No products found for this store.")
                continue

            # Use annotations for efficiency
            stats = products.aggregate(
                has_barcode_count=Count('pk', filter=Q(barcode__isnull=False) & ~Q(barcode='')),
                has_sku_count=Count('pk', filter=Q(company_skus__has_key='coles')),
                has_both_count=Count('pk', filter=(Q(barcode__isnull=False) & ~Q(barcode='')) & Q(company_skus__has_key='coles'))
            )

            has_barcode = stats['has_barcode_count']
            has_sku = stats['has_sku_count']
            has_both = stats['has_both_count']

            # Update overall counters
            overall_total_products += total_products
            overall_has_barcode += has_barcode
            overall_has_sku += has_sku
            overall_has_both += has_both

            # Calculate percentages
            perc_barcode = (has_barcode / total_products) * 100 if total_products > 0 else 0
            perc_sku = (has_sku / total_products) * 100 if total_products > 0 else 0
            
            perc_barcode_given_sku = (has_both / has_sku) * 100 if has_sku > 0 else 0
            perc_sku_given_barcode = (has_both / has_barcode) * 100 if has_barcode > 0 else 0

            self.stdout.write(f"  - Total Products: {total_products}")
            self.stdout.write(f"  - Have Barcode: {has_barcode} ({perc_barcode:.2f}%)")
            self.stdout.write(f"  - Have Coles SKU: {has_sku} ({perc_sku:.2f}%)")
            self.stdout.write(f"  - Of those with a SKU, {perc_barcode_given_sku:.2f}% also have a Barcode.")
            self.stdout.write(f"  - Of those with a Barcode, {perc_sku_given_barcode:.2f}% also have a Coles SKU.")

        # --- Overall Summary ---
        self.stdout.write(self.style.SUCCESS("\n--- Overall Coles Data Quality Summary ---"))
        
        # Calculate overall percentages
        overall_perc_barcode = (overall_has_barcode / overall_total_products) * 100 if overall_total_products > 0 else 0
        overall_perc_sku = (overall_has_sku / overall_total_products) * 100 if overall_total_products > 0 else 0
        
        overall_perc_barcode_given_sku = (overall_has_both / overall_has_sku) * 100 if overall_has_sku > 0 else 0
        overall_perc_sku_given_barcode = (overall_has_both / overall_has_barcode) * 100 if overall_has_barcode > 0 else 0

        self.stdout.write(f"  - Total Unique Products Across All Stores: {overall_total_products}")
        self.stdout.write(f"  - Have Barcode: {overall_has_barcode} ({overall_perc_barcode:.2f}%)")
        self.stdout.write(f"  - Have Coles SKU: {overall_has_sku} ({overall_perc_sku:.2f}%)")
        self.stdout.write(f"  - Of all products with a SKU, {overall_perc_barcode_given_sku:.2f}% also have a Barcode.")
        self.stdout.write(f"  - Of all products with a Barcode, {overall_perc_sku_given_barcode:.2f}% also have a Coles SKU.")
        self.stdout.write(self.style.SUCCESS("--- Analysis Complete ---"))
