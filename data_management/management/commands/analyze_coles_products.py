from django.core.management.base import BaseCommand
from django.db.models import Q
from products.models import Product

class Command(BaseCommand):
    help = 'Analyzes Coles products in the database for barcode information.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles Product Analysis ---"))

        # Find all products associated with Coles by checking the company_skus field.
        coles_products = Product.objects.filter(skus__company__name__iexact='Coles')
        total_coles_products = coles_products.count()

        if total_coles_products == 0:
            self.stdout.write(self.style.WARNING("No Coles products found in the database."))
            return

        # Filter for products that have a non-null and non-empty barcode.
        with_barcode = coles_products.filter(barcode__isnull=False).exclude(barcode__exact='')
        with_barcode_count = with_barcode.count()

        # Filter for products that have a null or empty barcode.
        without_barcode = coles_products.filter(Q(barcode__isnull=True) | Q(barcode__exact=''))
        without_barcode_count = without_barcode.count()

        # --- Detailed Breakdown ---

        # This is an inconsistent state and should ideally be zero.
        with_barcode_and_flag_true = with_barcode.filter(has_no_coles_barcode=True).count()

        # This is the expected state for products with a barcode.
        with_barcode_and_flag_false = with_barcode.filter(has_no_coles_barcode=False).count()

        # This is the expected state for products that have been processed and confirmed to have no barcode.
        without_barcode_and_flag_true = without_barcode.filter(has_no_coles_barcode=True).count()

        # This represents products that are missing a barcode but have not been flagged.
        # These might be new products that haven't been through the barcode scraper or an error state.
        without_barcode_and_flag_false = without_barcode.filter(has_no_coles_barcode=False).count()

        # --- Output Results ---
        self.stdout.write(f"Total Coles Products: {total_coles_products}")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Products WITH a barcode: {with_barcode_count}")
        self.stdout.write(f"  - (Contradiction) AND has_no_coles_barcode=True:  {with_barcode_and_flag_true}")
        self.stdout.write(f"  - (Correct)       AND has_no_coles_barcode=False: {with_barcode_and_flag_false}")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Products WITHOUT a barcode: {without_barcode_count}")
        self.stdout.write(f"  - (Correctly Flagged) AND has_no_coles_barcode=True:  {without_barcode_and_flag_true}")
        self.stdout.write(f"  - (Needs Update)      AND has_no_coles_barcode=False: {without_barcode_and_flag_false}")
        self.stdout.write(self.style.SUCCESS("--- Overall Analysis Complete ---"))

        self.stdout.write(self.style.SUCCESS("\n--- Starting Per-Store Analysis ---"))
        
        from companies.models import Store, Company
        from products.models import Price

        try:
            coles_company = Company.objects.get(name__iexact='coles')
            all_coles_stores = Store.objects.filter(company=coles_company)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR("Could not find 'Coles' company in the database."))
            return

        for store in all_coles_stores:
            self.stdout.write(f"\n--- Analyzing Store: {store.store_name} ({store.store_id}) ---")
            
            # Find product IDs associated with the current store through the Price model
            product_ids = Price.objects.filter(store=store).values_list('product_id', flat=True).distinct()
            store_products = Product.objects.filter(pk__in=product_ids)
            total_store_products = store_products.count()

            if total_store_products == 0:
                continue

            with_barcode_store = store_products.filter(barcode__isnull=False).exclude(barcode__exact='')
            with_barcode_count_store = with_barcode_store.count()

            without_barcode_store = store_products.filter(Q(barcode__isnull=True) | Q(barcode__exact=''))
            without_barcode_count_store = without_barcode_store.count()

            with_barcode_and_flag_true_store = with_barcode_store.filter(has_no_coles_barcode=True).count()
            with_barcode_and_flag_false_store = with_barcode_store.filter(has_no_coles_barcode=False).count()

            without_barcode_and_flag_true_store = without_barcode_store.filter(has_no_coles_barcode=True).count()
            without_barcode_and_flag_false_store = without_barcode_store.filter(has_no_coles_barcode=False).count()

            self.stdout.write(f"Total Products for this store: {total_store_products}")
            self.stdout.write("-" * 30)
            self.stdout.write(f"Products WITH a barcode: {with_barcode_count_store}")
            self.stdout.write(f"  - (Contradiction) AND has_no_coles_barcode=True:  {with_barcode_and_flag_true_store}")
            self.stdout.write(f"  - (Correct)       AND has_no_coles_barcode=False: {with_barcode_and_flag_false_store}")
            self.stdout.write("-" * 30)
            self.stdout.write(f"Products WITHOUT a barcode: {without_barcode_count_store}")
            self.stdout.write(f"  - (Correctly Flagged) AND has_no_coles_barcode=True:  {without_barcode_and_flag_true_store}")
            self.stdout.write(f"  - (Needs Update)      AND has_no_coles_barcode=False: {without_barcode_and_flag_false_store}")

        self.stdout.write(self.style.SUCCESS("\n--- Per-Store Analysis Complete ---"))

