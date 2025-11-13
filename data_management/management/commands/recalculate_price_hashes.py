import os
import json
from django.core.management.base import BaseCommand
from scraping.utils.product_scraping_utils.price_hasher import generate_price_hash

class Command(BaseCommand):
    help = 'Recalculates the price_hash for all product .jsonl files in a given directory.'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='The path to the directory containing the product files.')

    def handle(self, *args, **options):
        directory_path = options['directory']

        if not os.path.isdir(directory_path):
            self.stderr.write(self.style.ERROR(f"Directory not found: {directory_path}"))
            return

        self.stdout.write(f"Starting price hash recalculation for files in: {directory_path}")

        for root, _, files in os.walk(directory_path):
            for filename in files:
                if filename.endswith('.jsonl'):
                    file_path = os.path.join(root, filename)
                    self.stdout.write(f"  - Processing file: {file_path}")
                    
                    try:
                        updated_lines = []
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    data = json.loads(line)
                                    product_dict = data.get('product')
                                    if product_dict:
                                        # Recalculate the hash using the updated utility
                                        new_hash = generate_price_hash(product_dict)
                                        # Update the hash in the dictionary
                                        data['product']['price_hash'] = new_hash
                                    
                                    updated_lines.append(json.dumps(data))
                                except json.JSONDecodeError:
                                    self.stderr.write(self.style.WARNING(f"    - Skipping malformed JSON line in {filename}"))
                                    updated_lines.append(line.strip()) # Keep malformed line as is

                        # Write the updated content back to the file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            for line in updated_lines:
                                f.write(line + '\n')

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"    - Failed to process file {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS("Finished recalculating all price hashes."))
