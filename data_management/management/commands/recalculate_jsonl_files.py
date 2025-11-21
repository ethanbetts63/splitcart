import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from scraping.utils.product_scraping_utils.DataCleanerAldi import DataCleanerAldi
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga
from scraping.utils.product_scraping_utils.DataCleanerWoolworths import DataCleanerWoolworths

class Command(BaseCommand):
    help = 'Recalculates all .jsonl files in the product_jsonl directory using the latest normalization logic.'

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        self.stdout.write(self.style.SUCCESS("--- Starting Surgical Recalculation of JSONL Files ---"))
        
        product_dir = os.path.join(settings.BASE_DIR, 'product_jsonl')
        
        if not os.path.isdir(product_dir):
            self.stderr.write(self.style.ERROR(f"Directory not found: {product_dir}"))
            return

        cleaner_map = {
            'aldi': DataCleanerAldi,
            'coles': DataCleanerColes,
            'iga': DataCleanerIga,
            'woolworths': DataCleanerWoolworths,
        }
        
        # This function is needed to recalculate the hash
        from scraping.utils.product_scraping_utils.price_hasher import generate_price_hash
        from datetime import datetime

        jsonl_files = [os.path.join(root, file) for root, _, files in os.walk(product_dir) for file in files if file.endswith('.jsonl')]

        if not jsonl_files:
            self.stdout.write(self.style.WARNING("No .jsonl files found to process."))
            return

        self.stdout.write(f"Found {len(jsonl_files)} .jsonl files to process.")

        # Create dummy cleaner instances once
        dummy_cleaners = {}
        for company_name, CleanerClass in cleaner_map.items():
            dummy_cleaners[company_name] = CleanerClass(
                raw_product_list=[], company=company_name, store_name='', 
                store_id='', state=None, timestamp=datetime.now()
            )

        for file_path in jsonl_files:
            filename = os.path.basename(file_path)
            try:
                self.stdout.write(f"Processing file: {filename}")

                products = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            products.append(json.loads(line))
                
                if not products:
                    self.stdout.write(self.style.WARNING(f"  - File is empty. Skipping."))
                    continue

                updated_products = []
                for product in products:
                    company_name = product.get('company', '').lower()
                    dummy_cleaner = dummy_cleaners.get(company_name)

                    if not dummy_cleaner:
                        # If no cleaner, we can't process, so just keep the product as is
                        updated_products.append(product)
                        continue
                    
                    # This dictionary contains the fields needed by the normalizer
                    price_data_for_recalc = {
                        'per_unit_price_value': product.get('per_unit_price_value'),
                        'per_unit_price_measure': product.get('per_unit_price_measure'),
                        'per_unit_price_string': product.get('per_unit_price_string')
                    }

                    # Use the method from our dummy cleaner instance
                    new_price_info = dummy_cleaner._get_standardized_unit_price_info(price_data_for_recalc)

                    # Update the product dictionary with the new values
                    product['unit_price'] = new_price_info.get('unit_price')
                    product['unit_of_measure'] = new_price_info.get('unit_of_measure')
                    
                    # IMPORTANT: The price_hash also needs to be recalculated
                    product['price_hash'] = generate_price_hash(product)

                    updated_products.append(product)

                # Write the updated products back to the file in JSONL format
                with open(file_path, 'w', encoding='utf-8') as f:
                    for product in updated_products:
                        f.write(json.dumps(product) + '\n')
                
                self.stdout.write(self.style.SUCCESS(f"  - Successfully recalculated and saved {len(updated_products)} products."))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  - An error occurred while processing {filename}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("--- Finished Recalculation ---"))
