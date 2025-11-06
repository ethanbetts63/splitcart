
import os
import json
from django.core.management.base import BaseCommand
from data_management.utils.price_hasher import generate_price_hash

class Command(BaseCommand):
    help = 'Backfills the price_hash for products in existing .jsonl files.'

    def handle(self, *args, **options):
        target_dir = r'C:\Users\ethan\coding\splitcart\temp_jsonl_product_storage'
        self.stdout.write(self.style.SUCCESS(f'--- Starting backfill process for directory: {target_dir} ---'))

        if not os.path.isdir(target_dir):
            self.stderr.write(self.style.ERROR(f'Directory not found: {target_dir}'))
            return

        file_count = 0
        for root, _, files in os.walk(target_dir):
            for filename in files:
                if filename.endswith('.jsonl'):
                    file_path = os.path.join(root, filename)
                    file_count += 1
                    self.stdout.write(f'Processing file: {file_path}')
                    
                    updated_lines = []
                    lines_processed = 0
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                lines_processed += 1
                                try:
                                    data = json.loads(line)
                                    product_data = data.get('product')
                                    metadata = data.get('metadata')

                                    if not all([product_data, metadata, metadata.get('store_id')]):
                                        # If data is malformed, keep the original line
                                        updated_lines.append(line.strip())
                                        continue

                                    # Convert all empty string fields to None to ensure consistency
                                    for key, value in product_data.items():
                                        if isinstance(value, str) and not value.strip():
                                            product_data[key] = None

                                    # Remove keys with None values to mimic the final cleaning step
                                    product_data = {k: v for k, v in product_data.items() if v is not None}
                                    data['product'] = product_data
                                    
                                    # Generate and add the hash
                                    price_hash = generate_price_hash(product_data, metadata['store_id'])
                                    product_data['price_hash'] = price_hash
                                    
                                    updated_lines.append(json.dumps(data))

                                except json.JSONDecodeError:
                                    # Keep the original line if it's not valid JSON
                                    updated_lines.append(line.strip())
                                    continue
                        
                        # Write the updated content back to the file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(updated_lines))
                        
                        self.stdout.write(self.style.SUCCESS(f'  Successfully processed {lines_processed} lines in {filename}'))

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'  Could not process file {filename}. Error: {e}'))

        self.stdout.write(self.style.SUCCESS(f'--- Backfill complete. Processed {file_count} files. ---'))
