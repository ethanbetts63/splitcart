from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Resets the has_no_coles_barcode flag to False for all Coles products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles Barcode Flag Reset ---"))

        # Find all products associated with Coles by checking the company_skus field.
        coles_products = Product.objects.filter(company_skus__has_key='coles')

        # Update the has_no_coles_barcode field to False for all found products
        updated_count = coles_products.update(has_no_coles_barcode=False)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully reset 'has_no_coles_barcode' to False for {updated_count} Coles products."
        ))
        self.stdout.write(self.style.SUCCESS("--- Coles Barcode Flag Reset Complete ---"))
