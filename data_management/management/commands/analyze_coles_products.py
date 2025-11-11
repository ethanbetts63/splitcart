from django.core.management.base import BaseCommand
from django.db.models import Q
from products.models import Product

class Command(BaseCommand):
    help = 'Analyzes Coles products in the database for barcode information.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles Product Analysis ---"))

        # Find all products associated with Coles by checking the company_skus field.
        coles_products = Product.objects.filter(company_skus__has_key='coles')
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
        self.stdout.write(self.style.SUCCESS("--- Analysis Complete ---"))
