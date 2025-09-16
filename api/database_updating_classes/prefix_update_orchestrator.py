import os
import json
from django.conf import settings
from products.models import ProductBrand, BrandPrefix
from api.database_updating_classes.variation_manager import VariationManager
from api.utils.product_normalizer import ProductNormalizer
from api.database_updating_classes.brand_translation_table_generator import BrandTranslationTableGenerator

class PrefixUpdateOrchestrator:
    """
    Orchestrates the process of updating brand prefix information from the GS1 scraper inbox.
    It updates the BrandPrefix model and reconciles any discovered brand name synonyms.
    """
    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'prefix_inbox')
        self.temp_storage_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'temp_prefix_storage')
        os.makedirs(self.temp_storage_path, exist_ok=True)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Prefix Database Updater ---"))
        
        all_files = [os.path.join(self.inbox_path, f) for f in os.listdir(self.inbox_path) if f.endswith('.jsonl')]
        if not all_files:
            self.command.stdout.write("Prefix inbox is empty. No new data to process.")
            return

        brand_reconciliation_list = []
        processed_files = []

        for file_path in all_files:
            self.command.stdout.write(f"--- Processing file: {os.path.basename(file_path)} ---")
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self._process_record(data, brand_reconciliation_list)
                    except json.JSONDecodeError:
                        self.command.stderr.write(self.command.style.ERROR(f"Skipping invalid JSON line in {os.path.basename(file_path)}"))
                        continue
            processed_files.append(file_path)

        if brand_reconciliation_list:
            self._reconcile_brands(brand_reconciliation_list)

            # Regenerate the brand synonym file from the database state
            BrandTranslationTableGenerator().run()

        self._move_processed_files(processed_files)
        self.command.stdout.write(self.command.style.SUCCESS("--- Prefix Database Updater finished ---"))

    def _process_record(self, data: dict, brand_reconciliation_list: list):
        target_brand_id = data.get('target_brand_id')
        confirmed_key = data.get('confirmed_license_key')
        confirmed_name = data.get('confirmed_company_name')
        target_brand_name = data.get('target_brand_name')

        if not all([target_brand_id, confirmed_key, confirmed_name, target_brand_name]):
            self.command.stderr.write(f"Skipping record due to missing data: {data}")
            return

        # --- Corrected Logic ---
        # 1. Get or create the brand based on its normalized name.
        normalized_name = ProductNormalizer._clean_value(confirmed_name)
        canonical_brand, _ = ProductBrand.objects.get_or_create(
            normalized_name=normalized_name,
            defaults={'name': confirmed_name}
        )

        # 2. Attach the BrandPrefix to the CANONICAL brand.
        BrandPrefix.objects.update_or_create(
            brand=canonical_brand,
            defaults={
                'confirmed_official_prefix': confirmed_key,
                'brand_name_gs1': confirmed_name
            }
        )

        # 3. If the scraped brand is different, queue it for merging.
        if confirmed_name.lower() != target_brand_name.lower():
            reconciliation_entry = {
                'canonical_brand_name': confirmed_name,
                'duplicate_brand_name': target_brand_name
            }
            if reconciliation_entry not in brand_reconciliation_list:
                brand_reconciliation_list.append(reconciliation_entry)
                self.command.stdout.write(f"  - Queued brand '{target_brand_name}' for merging into '{confirmed_name}'.")

    def _reconcile_brands(self, brand_reconciliation_list):
        self.command.stdout.write("--- Reconciling newly discovered brand synonyms ---")
        
        if not brand_reconciliation_list:
            return

        for item in brand_reconciliation_list:
            canonical_name = item['canonical_brand_name']
            duplicate_name = item['duplicate_brand_name']

            # Use normalized names for lookups
            norm_canonical = ProductNormalizer._clean_value(canonical_name)
            norm_duplicate = ProductNormalizer._clean_value(duplicate_name)

            try:
                with transaction.atomic():
                    canonical_brand = ProductBrand.objects.get(normalized_name=norm_canonical)
                    duplicate_brand = ProductBrand.objects.get(normalized_name=norm_duplicate)

                    if canonical_brand.id == duplicate_brand.id:
                        continue

                    # Merge name_variations lists
                    if duplicate_brand.name_variations:
                        if not canonical_brand.name_variations:
                            canonical_brand.name_variations = []
                        for variation in duplicate_brand.name_variations:
                            if variation not in canonical_brand.name_variations:
                                canonical_brand.name_variations.append(variation)
                    
                    # Merge normalized_name_variations lists
                    if duplicate_brand.normalized_name_variations:
                        if not canonical_brand.normalized_name_variations:
                            canonical_brand.normalized_name_variations = []
                        for norm_variation in duplicate_brand.normalized_name_variations:
                            if norm_variation not in canonical_brand.normalized_name_variations:
                                canonical_brand.normalized_name_variations.append(norm_variation)

                    # Add the duplicate's own names to the variations list
                    new_name_variation_entry = (duplicate_brand.name, 'gs1')
                    if new_name_variation_entry not in canonical_brand.name_variations:
                        canonical_brand.name_variations.append(new_name_variation_entry)
                    
                    if duplicate_brand.normalized_name not in canonical_brand.normalized_name_variations:
                        canonical_brand.normalized_name_variations.append(duplicate_brand.normalized_name)
                    
                    canonical_brand.save()
                    
                    # Delete the duplicate brand
                    duplicate_brand.delete()
                    
                    self.command.stdout.write(f"  - Merged brand '{duplicate_name}' into '{canonical_name}'.")

            except ProductBrand.DoesNotExist:
                self.command.stderr.write(f"Could not find brand for merge: {canonical_name} or {duplicate_name}. Skipping.")
                continue
            except Exception as e:
                self.command.stderr.write(f"Error merging brand '{duplicate_name}': {e}")
                continue

    def _move_processed_files(self, processed_files: list):
        self.command.stdout.write("--- Moving processed prefix files to temp storage ---")
        for file_path in processed_files:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(self.temp_storage_path, file_name)
                os.rename(file_path, destination_path)
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not move file {file_path}: {e}'))
