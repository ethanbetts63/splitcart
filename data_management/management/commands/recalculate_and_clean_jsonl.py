import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from data_management.utils.product_normalizer import ProductNormalizer

class Command(BaseCommand):
    help = 'Recalculates normalized_name_brand_size and cleans up obsolete fields in JSONL files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            help='The absolute path to the directory containing .jsonl files to process.'
        )

    def handle(self, *args, **options):
        directory_path = options['directory']
        if not directory_path:
            directory_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'product_inbox')

        self.stdout.write(self.style.SUCCESS(f"--- Starting JSONL file processing in: {directory_path} ---"))

        if not os.path.exists(directory_path):
            self.stdout.write(self.style.WARNING("Directory not found."))
            return

        for filename in os.listdir(directory_path):
            if filename.endswith('.jsonl'):
                file_path = os.path.join(directory_path, filename)
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

        self.stdout.write(self.style.SUCCESS("--- JSONL file processing complete ---"))