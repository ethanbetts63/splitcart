import os
import json
from django.conf import settings
from products.models import ProductBrand
from api.utils.product_normalizer import ProductNormalizer
from api.database_updating_classes.brand_translation_table_generator import BrandTranslationTableGenerator

class PrefixUpdateOrchestrator:
    """
    Orchestrates the process of updating brand prefix information from the GS1 scraper inbox.
    It reconciles any discovered brand name synonyms.
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

        # After processing all files, regenerate the translation table to reflect any new variations.
        self.command.stdout.write("--- Regenerating brand translation table ---")
        BrandTranslationTableGenerator().run()

        self._move_processed_files(processed_files)
        self.command.stdout.write(self.command.style.SUCCESS("--- Prefix Database Updater finished ---"))

    def _process_record(self, data: dict):
        target_brand_id = data.get('target_brand_id')
        confirmed_key = data.get('confirmed_license_key')
        confirmed_name = data.get('confirmed_company_name')
        target_brand_name = data.get('target_brand_name')

        if not all([target_brand_id, confirmed_key, confirmed_name, target_brand_name]):
            self.command.stderr.write(f"Skipping record due to missing data: {data}")
            return

        # If the official GS1 name and the name we scraped are the same, there's nothing to do.
        if confirmed_name.lower() == target_brand_name.lower():
            return

        # 1. Get or create the CANONICAL brand (from GS1 info)
        canonical_normalized_name = ProductNormalizer._clean_value(confirmed_name)
        canonical_brand, _ = ProductBrand.objects.get_or_create(
            normalized_name=canonical_normalized_name,
            defaults={'name': confirmed_name}
        )

        # 2. Get or create the VARIATION brand (the one we looked up)
        variation_normalized_name = ProductNormalizer._clean_value(target_brand_name)
        variation_brand, _ = ProductBrand.objects.get_or_create(
            normalized_name=variation_normalized_name,
            defaults={'name': target_brand_name}
        )
        
        # If they resolved to the same brand object (e.g. due to pre-existing translations), stop.
        if canonical_brand.id == variation_brand.id:
            return

        # 3. Add the variation info to the canonical brand's variation lists
        updated = False
        if not canonical_brand.name_variations:
            canonical_brand.name_variations = []
        new_name_variation_entry = variation_brand.name  # Using 'gs1' as the source
        if new_name_variation_entry not in canonical_brand.name_variations:
            canonical_brand.name_variations.append(new_name_variation_entry)
            updated = True

        if not canonical_brand.normalized_name_variations:
            canonical_brand.normalized_name_variations = []
        if variation_brand.normalized_name not in canonical_brand.normalized_name_variations:
            canonical_brand.normalized_name_variations.append(variation_brand.normalized_name)
            updated = True
        
        if updated:
            canonical_brand.save()
            self.command.stdout.write(f"  - Recorded '{variation_brand.name}' as a variation of '{canonical_brand.name}'.")

        # 4. Update the canonical brand directly with the confirmed prefix.
        canonical_brand.confirmed_official_prefix = confirmed_key
        canonical_brand.save(update_fields=['confirmed_official_prefix'])

        self.command.stdout.write(f"  - Set confirmed prefix for '{canonical_brand.name}' to '{confirmed_key}'.")

    def _move_processed_files(self, processed_files: list):
        self.command.stdout.write("--- Moving processed prefix files to temp storage ---")
        for file_path in processed_files:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(self.temp_storage_path, file_name)
                os.rename(file_path, destination_path)
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not move file {file_path}: {e}'))
