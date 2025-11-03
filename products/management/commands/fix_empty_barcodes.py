from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Sets empty string barcodes to NULL to fix unique constraint issues.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Finding products with empty string barcodes...'))
        products_to_update = Product.objects.filter(barcode='')
        count = products_to_update.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No products with empty string barcodes found.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {count} products to update. Setting barcode to NULL...'))
        products_to_update.update(barcode=None)
        self.stdout.write(self.style.SUCCESS('Successfully updated products.'))
