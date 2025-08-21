from django.core.management.base import BaseCommand
from products.models import Product
from django.db import transaction

class Command(BaseCommand):
    help = "Backfills the normalized_name_brand_size field for existing Product objects."

    def _clean_value(self, value):
        if value is None:
            return ''
        return str(value).strip().lower()

    def handle(self, *args, **options):
        self.stdout.write(self.style.SQL_FIELD("--- Backfilling normalized_name_brand_size field ---"))
        
        updated_count = 0
        total_products = Product.objects.count()

        # Use select_for_update to lock rows during update to prevent race conditions
        # Use batching to avoid loading all objects into memory at once
        batch_size = 1000
        products_to_update = []

        for product in Product.objects.iterator():
            normalized_value = self._clean_value(product.name) + "_" + \
                               self._clean_value(product.brand) + "_" + \
                               self._clean_value(" ".join(product.sizes) if product.sizes else "")
            
            if product.normalized_name_brand_size != normalized_value:
                product.normalized_name_brand_size = normalized_value
                products_to_update.append(product)

            if len(products_to_update) >= batch_size:
                with transaction.atomic():
                    Product.objects.bulk_update(products_to_update, ['normalized_name_brand_size'])
                updated_count += len(products_to_update)
                self.stdout.write(f"Processed {updated_count}/{total_products} products...")
                products_to_update = []
        
        # Update any remaining products in the last batch
        if products_to_update:
            with transaction.atomic():
                Product.objects.bulk_update(products_to_update, ['normalized_name_brand_size'])
            updated_count += len(products_to_update)

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully backfilled normalized_name_brand_size for {updated_count} products."))
        self.stdout.write(self.style.SUCCESS("Backfill complete."))
