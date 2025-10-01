import os
import json
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fixes the product data format in temp storage from image_url to image_url_pairs.'

    def handle(self, *args, **options):
        storage_path = r'C:\Users\ethan\coding\splitcart\scraping\data\temp_jsonl_product_storage'
        self.stdout.write(self.style.SUCCESS(f'Starting to fix product format in {storage_path}'))

        if not os.path.exists(storage_path):
            self.stderr.write(self.style.ERROR(f"Directory not found: {storage_path}"))
            return

        for filename in os.listdir(storage_path):
            if not filename.endswith('.jsonl'):
                continue

            file_path = os.path.join(storage_path, filename)
            self.stdout.write(f"Processing file: {filename}")
            
            updated_lines = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    try:
                        data = json.loads(line)
                        product_data = data.get('product', {})
                        metadata = data.get('metadata', {})

                        if 'image_url' in product_data and product_data['image_url']:
                            company = metadata.get('company')
                            image_url = product_data['image_url']

                            if company:
                                # Create the new image_url_pairs field
                                product_data['image_url_pairs'] = [[company, image_url]]
                            
                            # Remove the old image_url field
                            del product_data['image_url']
                        
                        # Ensure image_url_pairs exists even if image_url was null/empty
                        if 'image_url_pairs' not in product_data:
                            product_data['image_url_pairs'] = []

                        updated_lines.append(json.dumps(data))

                    except (json.JSONDecodeError, KeyError) as e:
                        self.stderr.write(self.style.WARNING(f"  - Skipping line due to error: {e}"))
                        updated_lines.append(line.strip()) # Keep corrupted lines as they are
                        continue

                # Write the updated lines back to the same file
                with open(file_path, 'w', encoding='utf-8') as f:
                    for updated_line in updated_lines:
                        f.write(updated_line + '\n')

                self.stdout.write(self.style.SUCCESS(f"  - Successfully updated {filename}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  - Failed to process {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS('Finished fixing product format.'))
