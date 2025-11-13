import os
import json
from django.conf import settings
from products.models import ProductBrand, Product
from data_management.utils.product_normalizer import ProductNormalizer
from data_management.database_updating_classes.product_updating.translation_table_generators.brand_translation_table_generator import BrandTranslationTableGenerator

class PrefixUpdateOrchestrator:
    """
    Orchestrates the process of updating brand prefix information from the GS1 scraper inbox.
    It reconciles any discovered brand name synonyms.
    """
    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'prefix_inbox')
        self.temp_storage_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'temp_prefix_storage')
        os.makedirs(self.temp_storage_path, exist_ok=True)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Prefix Database Updater ---"))
        
        all_files = [os.path.join(self.inbox_path, f) for f in os.listdir(self.inbox_path) if f.endswith('.jsonl')]
        if not all_files:
            self.command.stdout.write("Prefix inbox is empty. No new data to process.")
            return

        processed_files = []

        for file_path in all_files:
            self.command.stdout.write(f"--- Processing file: {os.path.basename(file_path)} ---")
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self._process_record(data)
                    except json.JSONDecodeError:
                        self.command.stderr.write(self.command.style.ERROR(f"Skipping invalid JSON line in {os.path.basename(file_path)}"))
                        continue
            processed_files.append(file_path)

        self.command.stdout.write(self.command.style.SUCCESS("--- Prefix Database Updater finished ---"))

    def _process_record(self, data: dict):
        confirmed_key = data.get('confirmed_license_key')
        confirmed_name = data.get('confirmed_company_name')

        if not all([confirmed_key, confirmed_name]):
            self.command.stderr.write(f"Skipping record due to missing prefix or name data: {data}")
            return

        # 1. Get or create the CANONICAL brand (from GS1 info)
        canonical_normalized_name = ProductNormalizer._clean_value(confirmed_name)
        canonical_brand, created = ProductBrand.objects.get_or_create(
            normalized_name=canonical_normalized_name,
            defaults={'name': confirmed_name}
        )
        if created:
            self.command.stdout.write(f"  - Created new canonical brand: '{confirmed_name}'")

        # Always ensure the prefix is set on the canonical brand
        if canonical_brand.confirmed_official_prefix != confirmed_key:
            canonical_brand.confirmed_official_prefix = confirmed_key
            canonical_brand.save(update_fields=['confirmed_official_prefix'])
            self.command.stdout.write(f"  - Set confirmed prefix for '{canonical_brand.name}' to '{confirmed_key}'.")

        # 2. Find all products with this prefix but an inconsistent brand
        inconsistent_products = Product.objects.select_related('brand').filter(
            barcode__startswith=confirmed_key
        ).exclude(brand=canonical_brand)

        if not inconsistent_products.exists():
            return

        # 3. Segregate products into brandless and incorrectly branded
        brandless_products_ids = []
        incorrect_brands = set()

        for product in inconsistent_products:
            if product.brand:
                incorrect_brands.add(product.brand)
            else:
                brandless_products_ids.append(product.id)

        # 4. Process incorrectly branded products by adding them as variations
        updated = False
        if incorrect_brands:
            self.command.stdout.write(f"  - Found {len(incorrect_brands)} incorrect brands to mark as variations.")
            if not canonical_brand.name_variations:
                canonical_brand.name_variations = []
            if not canonical_brand.normalized_name_variations:
                canonical_brand.normalized_name_variations = []

            for brand in incorrect_brands:
                if brand.name not in canonical_brand.name_variations:
                    canonical_brand.name_variations.append(brand.name)
                    updated = True
                    self.command.stdout.write(f"    - Recording '{brand.name}' as a name variation of '{canonical_brand.name}'.")

                if brand.normalized_name not in canonical_brand.normalized_name_variations:
                    canonical_brand.normalized_name_variations.append(brand.normalized_name)
                    updated = True

        if updated:
            canonical_brand.save()

        # 5. Process brandless products by linking them to the canonical brand
        if brandless_products_ids:
            self.command.stdout.write(f"  - Found {len(brandless_products_ids)} products with no brand. Linking them to '{canonical_brand.name}'.")
            Product.objects.filter(id__in=brandless_products_ids).update(brand=canonical_brand)


