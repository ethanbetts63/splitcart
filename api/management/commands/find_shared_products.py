from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Finds products that are explicitly linked to both Coles and Woolworths.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Searching for products linked to BOTH Coles and Woolworths ---"))

        # Find products that have a price from a store whose company is 'Coles'
        # AND have a price from a store whose company is 'Woolworths'.
        # The distinct() call is important to avoid counting the same product multiple times
        # if it has multiple prices at the same company.
        shared_products = Product.objects.filter(
            prices__store__company__name__iexact='Coles'
        ).filter(
            prices__store__company__name__iexact='Woolworths'
        ).distinct()

        count = shared_products.count()

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Found {count} shared product(s)."))
            for product in shared_products:
                self.stdout.write(f"  - ID: {product.id}, Name: {product.name}, Brand: {product.brand}, Size: {product.size}")
        else:
            self.stdout.write(self.style.WARNING("Found 0 products explicitly linked to both Coles and Woolworths."))

        self.stdout.write(self.style.SUCCESS("--- Diagnostic complete ---"))
