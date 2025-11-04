
import os
import json
from django.core.management.base import BaseCommand
from data_management.config import PRODUCT_INBOX_PATH
from data_management.utils.product_normalizer import ProductNormalizer

class Command(BaseCommand):
    help = 'Recalculates normalized_name_brand_size and cleans up obsolete fields in JSONL files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting JSONL file recalculation and cleanup ---"))

        if not os.path.exists(PRODUCT_INBOX_PATH):
            self.stdout.write(self.style.WARNING(f"Product inbox not found at: {PRODUCT_INBOX_PATH}"))
            return

        for filename in os.listdir(PRODUCT_INBOX_PATH):
            if filename.endswith('.jsonl'):
                file_path = os.path.join(PRODUCT_INBOX_PATH, filename)
                self.stdout.write(f"Processing file: {file_path}")
                
                processed_lines = []
                had_changes = False
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for line in lines:
                        try:
                            data = json.loads(line)
                            product_data = data.get('product')

                            if not product_data:
                                processed_lines.append(line.strip()) # Keep line if no product data
                                continue

                            # Instantiate the normalizer without a brand cache, mimicking the scraper
                            normalizer = ProductNormalizer(product_data, brand_cache=None)

                            # 1. Recalculate the normalized_name_brand_size field for consistency
                            new_normalized_string = normalizer.get_normalized_name_brand_size_string()
                            
                            if product_data.get('normalized_name_brand_size') != new_normalized_string:
                                product_data['normalized_name_brand_size'] = new_normalized_string
                                had_changes = True

                            # 2. Remove the obsolete 'normalized_name' field
                            if 'normalized_name' in product_data:
                                del product_data['normalized_name']
                                had_changes = True
                            
                            data['product'] = product_data
                            processed_lines.append(json.dumps(data))

                        except json.JSONDecodeError:
                            self.stdout.write(self.style.WARNING(f"  - Could not decode JSON from a line in {filename}. Skipping line."))
                            processed_lines.append(line.strip()) # Keep the original line if it's broken
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  - An unexpected error occurred processing a line: {e}"))
                            processed_lines.append(line.strip())

                    # Write the processed lines back to the file only if changes were made
                    if had_changes:
                        self.stdout.write(self.style.SUCCESS(f"  - Changes detected. Overwriting {filename}."))
                        with open(file_path, 'w', encoding='utf-8') as f:
                            for processed_line in processed_lines:
                                f.write(processed_line + '\n')
                    else:
                        self.stdout.write(f"  - No changes needed for {filename}.")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Could not process file {filename}. Error: {e}"))

        self.stdout.write(self.style.SUCCESS("--- JSONL file cleanup complete ---"))
