from django.core.management.base import BaseCommand
from products.models import Product, ProductBrand
from api.utils.product_normalizer import ProductNormalizer
import time

class Command(BaseCommand):
    help = 'Synchronizes the ProductBrand table with unique brand names from the Product table.'

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Synchronization ---"))

        self.stdout.write("Fetching unique brand names from products...")
        product_brands_raw = set(Product.objects.values_list('brand', flat=True).distinct())
        product_brands_raw.discard(None)
        product_brands_raw.discard('')

        self.stdout.write("Fetching existing normalized brands from brand table...")
        existing_normalized = set(ProductBrand.objects.values_list('normalized_name', flat=True))
        existing_normalized.discard(None)
        existing_normalized.discard('')

        self.stdout.write(f"Found {len(product_brands_raw)} unique raw brand strings to process.")

        new_brands_map = {}
        for raw_name in product_brands_raw:
            if not raw_name: continue
            
            normalizer = ProductNormalizer({'brand': raw_name, 'name': ''})
            normalized = normalizer.cleaned_brand
            
            if normalized and normalized not in existing_normalized and normalized not in new_brands_map:
                new_brands_map[normalized] = raw_name

        if not new_brands_map:
            self.stdout.write(self.style.SUCCESS("ProductBrand table is already up-to-date."))
            end_time = time.time()
            duration = end_time - start_time
            self.stdout.write(self.style.SUCCESS(f"--- Synchronization Complete in {duration:.2f} seconds ---"))
            return

        self.stdout.write(f"Found {len(new_brands_map)} new canonical brands to create. Bulk creating...")
        
        brands_to_create = []
        for normalized, raw in new_brands_map.items():
            brands_to_create.append(
                ProductBrand(name=raw, normalized_name=normalized)
            )
        
        ProductBrand.objects.bulk_create(brands_to_create)

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Synchronization Complete in {duration:.2f} seconds ---"))
        self.stdout.write(f"Successfully created {len(brands_to_create)} new brand entries.")