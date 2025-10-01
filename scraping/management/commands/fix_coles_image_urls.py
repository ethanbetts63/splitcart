import os
import json
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fixes the image_url for Coles products in the specified JSONL files.'

    def handle(self, *args, **options):
        storage_path = r'C:\Users\ethan\coding\splitcart\scraping\data\temp_jsonl_product_storage'
        self.stdout.write(self.style.SUCCESS(f'Starting to fix Coles image URLs in {storage_path}'))

        for filename in os.listdir(storage_path):
            if not filename.endswith('.jsonl') or 'coles' not in filename.lower():
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

                        # Double-check it's a Coles product from metadata
                        if metadata.get('company', '').lower() == 'coles':
                            sku = product_data.get('sku')
                            if sku:
                                new_image_url = f"https://productimages.coles.com.au/productimages/2/{sku}.jpg"
                                product_data['image_url'] = new_image_url
                        
                        updated_lines.append(json.dumps(data))

                    except json.JSONDecodeError:
                        # Keep corrupted or non-JSON lines as they are
                        updated_lines.append(line.strip())
                        continue

                # Write the updated lines back to the same file
                with open(file_path, 'w', encoding='utf-8') as f:
                    for updated_line in updated_lines:
                        f.write(updated_line + '\n')

                self.stdout.write(self.style.SUCCESS(f"  - Successfully updated {filename}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  - Failed to process {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS('Finished fixing Coles image URLs.'))
