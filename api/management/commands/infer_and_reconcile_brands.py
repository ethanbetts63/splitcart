import time
from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Product, ProductBrand, BrandPrefix
from api.database_updating_classes.variation_manager import VariationManager
from api.database_updating_classes.product_translation_table_generator import ProductTranslationTableGenerator

def find_longest_common_prefix(strs):
    if not strs:
        return ""
    shortest_str = min(strs, key=len)
    for i, char in enumerate(shortest_str):
        for other_str in strs:
            if other_str[i] != char:
                return shortest_str[:i]
    return shortest_str

def get_address_space(prefix_len):
    """Calculates the number of unique barcodes a prefix of a given length can support in EAN-13."""
    if not (7 <= prefix_len <= 12):
        return 0
    # EAN-13 has 13 digits. 1 is the check digit. The rest is prefix + item ref.
    item_ref_len = 12 - prefix_len
    return 10 ** item_ref_len

class Command(BaseCommand):
    help = 'Analyzes product barcodes to infer brand prefixes and reconciles brand names based on these inferences.'

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Inference and Reconciliation --- "))

        self._phase_one_infer_prefixes()
        self._phase_two_reconcile_brands()

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Full process complete in {duration:.2f} seconds ---"))

    def _phase_one_infer_prefixes(self):
        self.stdout.write(self.style.SQL_FIELD("--- Phase 1: Inferring Prefixes from Barcodes ---"))

        # Get brands that do NOT have a confirmed prefix already
        brands_with_confirmed_prefixes = BrandPrefix.objects.filter(confirmed_official_prefix__isnull=False).values_list('brand_id', flat=True)
        brands_to_analyze = ProductBrand.objects.exclude(id__in=brands_with_confirmed_prefixes)
        
        total_brands = brands_to_analyze.count()
        self.stdout.write(f"Found {total_brands} brands to analyze.")

        for i, brand in enumerate(brands_to_analyze.iterator()):
            if (i + 1) % 100 == 0:
                self.stdout.write(f"  - Processed {i + 1}/{total_brands} brands...")

            products = Product.objects.filter(brand=brand.name).exclude(barcode__isnull=True).exclude(barcode__exact='')
            product_count = products.count()
            barcodes = list(products.values_list('barcode', flat=True))

            if len(barcodes) < 2:
                continue

            lcp = find_longest_common_prefix(barcodes)
            if len(lcp) < 7: # GS1 prefixes are usually at least 7 digits
                continue

            # Find the longest plausible prefix using the address space rule
            longest_plausible_prefix = ""
            for length in range(len(lcp), 6, -1):
                address_space = get_address_space(length)
                if product_count < address_space:
                    longest_plausible_prefix = lcp[:length]
                    break
            
            if longest_plausible_prefix:
                BrandPrefix.objects.update_or_create(
                    brand=brand,
                    defaults={'longest_inferred_prefix': longest_plausible_prefix}
                )

        self.stdout.write(self.style.SUCCESS("--- Prefix inference complete ---"))

    def _phase_two_reconcile_brands(self):
        self.stdout.write(self.style.SQL_FIELD("--- Phase 2: Reconciling Brands from Inferred Prefixes ---"))

        prefixes_to_check = BrandPrefix.objects.filter(
            longest_inferred_prefix__isnull=False,
            confirmed_official_prefix__isnull=True # Only use inferred data
        ).select_related('brand').order_by('-longest_inferred_prefix') # Process longer prefixes first

        if not prefixes_to_check.exists():
            self.stdout.write("No inferred prefixes to check. Skipping reconciliation.")
            return

        reconciliation_list = []
        processed_products = set()

        for prefix_entry in prefixes_to_check.iterator():
            prefix = prefix_entry.longest_inferred_prefix
            canonical_brand = prefix_entry.brand

            # Find products that start with this prefix but have a different brand name
            inconsistent_products = Product.objects.filter(
                barcode__startswith=prefix
            ).exclude(brand=canonical_brand.name).exclude(id__in=processed_products)

            for product in inconsistent_products:
                reconciliation_entry = {
                    'canonical_brand_name': canonical_brand.name,
                    'duplicate_brand_name': product.brand
                }
                if reconciliation_entry not in reconciliation_list:
                    reconciliation_list.append(reconciliation_entry)
                processed_products.add(product.id)

        if not reconciliation_list:
            self.stdout.write("Found no brand discrepancies to reconcile.")
            return

        self.stdout.write(f"Found {len(reconciliation_list)} potential brand synonyms to merge.")
        variation_manager = VariationManager(self, unit_of_work=None)
        variation_manager.brand_reconciliation_list = reconciliation_list
        variation_manager.reconcile_brand_duplicates()

        # Regenerate the product name translation table
        ProductTranslationTableGenerator().run()

        self.stdout.write(self.style.SUCCESS("--- Brand reconciliation complete ---"))
