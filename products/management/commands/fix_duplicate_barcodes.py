from django.core.management.base import BaseCommand
from products.models import Product
from django.db.models import Count

class Command(BaseCommand):
    help = 'Finds duplicate barcodes and nullifies them to fix unique constraint issues.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Finding duplicate barcodes...'))
        
        # Find barcodes that are used by more than one product
        duplicate_barcodes = (
            Product.objects.values('barcode')
            .annotate(barcode_count=Count('barcode'))
            .filter(barcode_count__gt=1)
            .exclude(barcode__isnull=True)
            .exclude(barcode='')
        )

        if not duplicate_barcodes:
            self.stdout.write(self.style.SUCCESS('No duplicate barcodes found.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(duplicate_barcodes)} duplicate barcode(s).'))

        for item in duplicate_barcodes:
            barcode = item['barcode']
            self.stdout.write(self.style.WARNING(f'  - Processing duplicate barcode: {barcode}'))
            
            # Get all products with this duplicate barcode
            products_with_barcode = Product.objects.filter(barcode=barcode).order_by('id')
            
            # Keep the first product and nullify the barcode for the rest
            first_product = products_with_barcode.first()
            self.stdout.write(self.style.SUCCESS(f'    - Keeping barcode for product PK: {first_product.id}'))
            
            products_to_nullify = products_with_barcode.exclude(id=first_product.id)
            for product in products_to_nullify:
                self.stdout.write(self.style.WARNING(f'    - Nullifying barcode for product PK: {product.id}'))
                product.barcode = None
                product.save()

        self.stdout.write(self.style.SUCCESS('Successfully processed duplicate barcodes.'))
