import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Removes keys with null values from product data in JSONL files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            help='The absolute path to the directory containing .jsonl files to process.',
            required=True
        )

    def handle(self, *args, **options):
        directory_path = options['directory']

        self.stdout.write(self.style.SUCCESS(f"--- Starting JSONL null value removal in: {directory_path} ---"))

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
                                processed_lines.append(line.strip())
                                continue

                            original_key_count = len(product_data)
                            # Create a new dictionary without the null values
                            cleaned_product_data = {k: v for k, v in product_data.items() if v is not None}
                            
                            if len(cleaned_product_data) != original_key_count:
                                had_changes = True

                            data['product'] = cleaned_product_data
                            processed_lines.append(json.dumps(data))

                        except json.JSONDecodeError:
                            self.stdout.write(self.style.WARNING(f"  - Could not decode JSON from a line in {filename}. Skipping line."))
                            processed_lines.append(line.strip())
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  - An unexpected error occurred processing a line: {e}"))
                            processed_lines.append(line.strip())

                    if had_changes:
                        self.stdout.write(self.style.SUCCESS(f"  - Null values found and removed. Overwriting {filename}."))
                        with open(file_path, 'w', encoding='utf-8') as f:
                            for processed_line in processed_lines:
                                f.write(processed_line + '\n')
                    else:
                        self.stdout.write(f"  - No null values found in {filename}.")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Could not process file {filename}. Error: {e}"))

        self.stdout.write(self.style.SUCCESS("--- JSONL null value removal complete ---"))
