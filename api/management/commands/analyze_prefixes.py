from django.core.management.base import BaseCommand
from products.models import Product, ProductBrand, BrandPrefix
import time

def find_longest_common_prefix(strs):
    if not strs:
        return ""
    strs = [s for s in strs if isinstance(s, str)]
    if not strs:
        return ""
    shortest_str = min(strs, key=len)
    for i, char in enumerate(shortest_str):
        for other_str in strs:
            if other_str[i] != char:
                return shortest_str[:i]
    return shortest_str

class Command(BaseCommand):
    help = 'Analyzes product barcodes to populate the BrandPrefix table.'

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Prefix Analysis ---"))

        self.stdout.write("Clearing existing BrandPrefix data...")
        BrandPrefix.objects.all().delete()

        brands = ProductBrand.objects.all()
        total_brands = brands.count()
        self.stdout.write(f"Found {total_brands} brands to analyze...")

        prefixes_to_create = []
        prefixes_added_this_run = set()

        for i, brand in enumerate(brands):
            products = Product.objects.filter(brand=brand.name).exclude(barcode__isnull=True).exclude(barcode__exact='')
            barcodes = list(products.values_list('barcode', flat=True))
            
            product_count = len(barcodes)
            if product_count < 2:
                continue

            lcp = find_longest_common_prefix(barcodes)
            
            plausible_prefixes = [lcp[:i] for i in range(6, min(len(lcp), 11) + 1)]

            if not plausible_prefixes:
                continue

            for prefix_str in plausible_prefixes:
                if prefix_str not in prefixes_added_this_run:
                    is_grouping = (prefix_str == plausible_prefixes[-1])
                    is_official = (prefix_str == plausible_prefixes[0])
                    
                    prefixes_to_create.append(
                        BrandPrefix(
                            prefix=prefix_str,
                            brand=brand,
                            is_grouping_prefix=is_grouping,
                            is_likely_official=is_official,
                            product_count=product_count,
                            prefix_length=len(prefix_str)
                        )
                    )
                    prefixes_added_this_run.add(prefix_str)
            
            if (i + 1) % 100 == 0:
                self.stdout.write(f"Processed {i + 1}/{total_brands} brands...")

        if prefixes_to_create:
            self.stdout.write(f"Found {len(prefixes_to_create)} potential prefixes. Bulk creating...")
            BrandPrefix.objects.bulk_create(prefixes_to_create)

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Analysis Complete in {duration:.2f} seconds ---"))