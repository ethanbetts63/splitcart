from django.core.management.base import BaseCommand
from products.models import Product
from api.utils.product_normalizer import ProductNormalizer
from django.db import transaction

class Command(BaseCommand):
    help = 'Backfills the `sizes` field for all existing products using the latest normalization logic.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting backfill process for product sizes..."))

        products_to_update = []
        batch_size = 1000
        total_processed = 0
        total_updated = 0

        # Use an iterator to handle a large number of products without high memory usage
        all_products = Product.objects.all().iterator()

        for product in all_products:
            total_processed += 1

            # The ProductNormalizer expects a dictionary of product data
            product_data = {
                'name': product.name,
                'brand': product.brand,
                'size': product.size,
            }
            normalizer = ProductNormalizer(product_data)
            
            # The standardized_sizes property contains the new, fully de-duplicated list
            new_sizes = normalizer.standardized_sizes
            old_sizes = product.sizes

            # Only update if the sizes have actually changed
            # We sort both lists to ensure the comparison is accurate regardless of order
            if sorted(old_sizes) != sorted(new_sizes):
                product.sizes = new_sizes
                products_to_update.append(product)
                total_updated += 1

            if len(products_to_update) >= batch_size:
                self.stdout.write(f"Processed {total_processed} products. Updating batch of {len(products_to_update)}...")
                with transaction.atomic():
                    Product.objects.bulk_update(products_to_update, ['sizes'])
                products_to_update = []

        # Update any remaining products in the last batch
        if products_to_update:
            self.stdout.write(f"Processed {total_processed} products. Updating final batch of {len(products_to_update)}...")
            with transaction.atomic():
                Product.objects.bulk_update(products_to_update, ['sizes'])

        self.stdout.write(self.style.SUCCESS("\nBackfill complete."))
        self.stdout.write(f"  - Total products processed: {total_processed}")
        self.stdout.write(f"  - Total products updated: {total_updated}")
