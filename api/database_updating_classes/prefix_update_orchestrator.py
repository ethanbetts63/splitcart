import os
import json
from django.conf import settings
from products.models import ProductBrand, BrandPrefix
from api.database_updating_classes.variation_manager import VariationManager
from api.utils.product_normalizer import ProductNormalizer

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
            from api.utils.synonym_utils.brand_synonym_generator import generate_brand_synonym_file
            generate_brand_synonym_file(self.command)

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
        # 1. Get or create the CANONICAL brand first.
        canonical_brand, _ = ProductBrand.objects.get_or_create(
            name=confirmed_name,
            defaults={'normalized_name': ProductNormalizer({'brand': confirmed_name, 'name': ''}).get_normalized_brand_key()}
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
        # We can reuse the existing VariationManager for this
        variation_manager = VariationManager(self.command, unit_of_work=None)
        # Pass a copy of the list so the original isn't cleared by the manager
        variation_manager.brand_reconciliation_list = brand_reconciliation_list.copy()
        variation_manager.reconcile_brand_duplicates()

    def _move_processed_files(self, processed_files: list):
        self.command.stdout.write("--- Moving processed prefix files to temp storage ---")
        for file_path in processed_files:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(self.temp_storage_path, file_name)
                os.rename(file_path, destination_path)
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not move file {file_path}: {e}'))
