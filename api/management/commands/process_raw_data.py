import os
import json
import re
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Processes raw JSON files, combines them by category, saves to a structured directory, and cleans up raw files on success.'

    def add_arguments(self, parser):
        parser.add_argument(
            'store_name',
            nargs='?',
            type=str,
            help='Optional: The name of the store to process (e.g., "coles"). Processes all if omitted.',
            default=None
        )

    def handle(self, *args, **options):
        store_to_process = options['store_name']
        
        # Correctly locate the 'api' app directory
        api_app_path = os.path.join(settings.BASE_DIR, 'api')
        raw_data_path = os.path.join(api_app_path, 'data', 'raw_data')
        processed_data_path = os.path.join(api_app_path, 'data', 'processed_data')

        if not os.path.isdir(raw_data_path):
            self.stdout.write(self.style.ERROR(f"Raw data directory not found at: {raw_data_path}"))
            return

        file_pattern = re.compile(r'^(?P<store>\w+)_(?P<cat>[\w-]+)_page-(?P<page>\d+)_(?P<date>\d{4}-\d{2}-\d{2})_.*\.json$')
        
        all_files = os.listdir(raw_data_path)
        
        stores_to_process = []
        if store_to_process:
            stores_to_process.append(store_to_process.lower())
        else:
            self.stdout.write(self.style.SUCCESS("No store specified. Processing all available stores..."))
            found_stores = set(match.group('store') for f in all_files if (match := file_pattern.match(f)))
            stores_to_process = list(found_stores)

        if not stores_to_process:
            self.stdout.write(self.style.WARNING("No raw data files found to process."))
            return

        for store_name in stores_to_process:
            self.stdout.write(self.style.SUCCESS(f"\n--- Starting data processing for '{store_name}' ---"))

            files_by_date = defaultdict(list)
            for filename in all_files:
                match = file_pattern.match(filename)
                if match and match.group('store') == store_name:
                    files_by_date[match.group('date')].append(filename)

            if not files_by_date:
                self.stdout.write(self.style.WARNING(f"No raw data files found for '{store_name}'."))
                continue

            latest_date = sorted(files_by_date.keys(), reverse=True)[0]
            self.stdout.write(f"Processing latest scrape from: {latest_date}")
            
            files_to_process_for_cleanup = files_by_date[latest_date]
            files_by_category = defaultdict(list)
            for filename in files_to_process_for_cleanup:
                match = file_pattern.match(filename)
                if match:
                    files_by_category[match.group('cat')].append(filename)

            # --- Atomic Processing Flag ---
            all_categories_processed_successfully = True

            for category, page_files in files_by_category.items():
                self.stdout.write(f"\nProcessing category: '{category}'...")
                
                all_products = []
                sorted_files = sorted(page_files, key=lambda f: int(file_pattern.match(f).group('page')))

                for filename in sorted_files:
                    file_path = os.path.join(raw_data_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            page_products = json.load(f)
                            all_products.extend(page_products)
                    except (json.JSONDecodeError, IOError) as e:
                        self.stdout.write(self.style.ERROR(f"  - Could not read or parse {filename}. Error: {e}"))
                        all_categories_processed_successfully = False
                        break # Stop processing this category
                
                if not all_categories_processed_successfully:
                    break # Stop processing other categories if one failed

                if not all_products:
                    self.stdout.write(self.style.WARNING(f"  - No products found for category '{category}'. Skipping."))
                    continue

                # --- Corrected Directory Logic ---
                target_dir = os.path.join(processed_data_path, store_name, latest_date)
                os.makedirs(target_dir, exist_ok=True)
                
                output_filename = f"{category}.json"
                output_filepath = os.path.join(target_dir, output_filename)
                
                try:
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        json.dump(all_products, f, indent=4)
                    self.stdout.write(self.style.SUCCESS(f"  - Combined {len(all_products)} products and saved to {output_filepath}"))
                except IOError as e:
                    self.stdout.write(self.style.ERROR(f"  - FAILED to save combined file for '{category}'. Error: {e}"))
                    all_categories_processed_successfully = False
                    break

            # --- Atomic Deletion Step ---
            if all_categories_processed_successfully:
                self.stdout.write(self.style.SUCCESS(f"\nAll categories for {latest_date} processed successfully. Deleting raw files..."))
                for filename in files_to_process_for_cleanup:
                    try:
                        os.remove(os.path.join(raw_data_path, filename))
                        self.stdout.write(f"  - Deleted {filename}")
                    except OSError as e:
                        self.stdout.write(self.style.ERROR(f"  - FAILED to delete {filename}. Error: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"\nProcessing failed for {latest_date}. Raw files have been kept for inspection."))

        self.stdout.write(self.style.SUCCESS(f"\n--- All data processing complete ---"))
