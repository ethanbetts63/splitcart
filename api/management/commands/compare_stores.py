import os
import json
from django.core.management.base import BaseCommand
from datetime import datetime

class Command(BaseCommand):
    help = 'Compares product prices and availability between two stores of the same company from the latest processed data.'

    def add_arguments(self, parser):
        parser.add_argument('company_name', type=str, help='The company to compare stores for (e.g., woolworths).')
        parser.add_argument('store_a_name', type=str, help='The name of the first store.')
        parser.add_argument('store_b_name', type=str, help='The name of the second store.')

    def handle(self, *args, **options):
        company_name = options['company_name']
        store_a_name = options['store_a_name']
        store_b_name = options['store_b_name']

        if company_name.lower() != 'woolworths':
            self.stdout.write(self.style.ERROR("This command currently only supports 'woolworths'."))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Comparing Woolworths Stores: '{store_a_name}' vs '{store_b_name}' ---"))

        processed_data_path = os.path.join('api', 'data', 'processed_data')

        try:
            latest_file_a = self._find_latest_processed_file(processed_data_path, company_name, store_a_name)
            latest_file_b = self._find_latest_processed_file(processed_data_path, company_name, store_b_name)
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            return

        self.stdout.write(f"Found data for '{store_a_name}': {os.path.basename(latest_file_a)}")
        self.stdout.write(f"Found data for '{store_b_name}': {os.path.basename(latest_file_b)}")

        products_a = self._load_products_from_file(latest_file_a)
        products_b = self._load_products_from_file(latest_file_b)

        # Use Woolworths' 'Stockcode' as the unique identifier
        products_a_by_sku = {p['id']: p for p in products_a}
        products_b_by_sku = {p['id']: p for p in products_b}

        skus_a = set(products_a_by_sku.keys())
        skus_b = set(products_b_by_sku.keys())

        common_skus = skus_a.intersection(skus_b)
        exclusive_skus_a = skus_a - skus_b
        exclusive_skus_b = skus_b - skus_a

        # --- Analysis ---
        price_differences = []
        for sku in common_skus:
            prod_a = products_a_by_sku[sku]
            prod_b = products_b_by_sku[sku]
            if prod_a['price'] != prod_b['price']:
                price_differences.append({
                    'name': prod_a.get('name', 'N/A'),
                    'size': prod_a.get('size', 'N/A'),
                    'price_a': prod_a['price'],
                    'price_b': prod_b['price']
                })

        # --- Reporting ---
        self.stdout.write(self.style.SUCCESS("\n--- Comparison Report ---"))
        self.stdout.write(f"Total Products in '{store_a_name}': {len(skus_a)}")
        self.stdout.write(f"Total Products in '{store_b_name}': {len(skus_b)}")
        self.stdout.write(f"Common Products: {len(common_skus)}")
        self.stdout.write(f"Exclusive to '{store_a_name}': {len(exclusive_skus_a)}")
        self.stdout.write(f"Exclusive to '{store_b_name}': {len(exclusive_skus_b)}")

        self.stdout.write(self.style.SUCCESS("\n--- Price Comparison (Common Products) ---"))
        self.stdout.write(f"Products with identical prices: {len(common_skus) - len(price_differences)}")
        self.stdout.write(f"Products with different prices: {len(price_differences)}")

        if price_differences:
            self.stdout.write(self.style.WARNING("\n--- Products with Price Differences ---"))
            for diff in price_differences[:20]: # Limit output
                self.stdout.write(f"  - {diff['name']} ({diff['size']}) | {store_a_name}: ${diff['price_a']:.2f} | {store_b_name}: ${diff['price_b']:.2f}")
            if len(price_differences) > 20:
                self.stdout.write("  ...")

        if exclusive_skus_a:
            self.stdout.write(self.style.SUCCESS(f"\n--- Sample of Products Exclusive to '{store_a_name}' ---"))
            for sku in list(exclusive_skus_a)[:10]: # Limit output
                prod = products_a_by_sku[sku]
                self.stdout.write(f"  - {prod.get('name', 'N/A')} ({prod.get('size', 'N/A')}) - ${prod.get('price', 0.0):.2f}")
            if len(exclusive_skus_a) > 10:
                self.stdout.write("  ...")

        if exclusive_skus_b:
            self.stdout.write(self.style.SUCCESS(f"\n--- Sample of Products Exclusive to '{store_b_name}' ---"))
            for sku in list(exclusive_skus_b)[:10]: # Limit output
                prod = products_b_by_sku[sku]
                self.stdout.write(f"  - {prod.get('name', 'N/A')} ({prod.get('size', 'N/A')}) - ${prod.get('price', 0.0):.2f}")
            if len(exclusive_skus_b) > 10:
                self.stdout.write("  ...")

    def _find_latest_processed_file(self, base_path, company, store_name):
        """Finds the most recent processed data file for a given store."""
        store_files = []
        file_prefix = f"{company}_{store_name}".lower()
        for filename in os.listdir(base_path):
            if filename.startswith(file_prefix) and filename.endswith('.json'):
                try:
                    # Extract date from filename like 'woolworths_richmond_2023-10-27.json'
                    date_str = filename.replace(file_prefix + '_', '').replace('.json', '')
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    store_files.append((file_date, os.path.join(base_path, filename)))
                except ValueError:
                    continue # Ignore files that don't match the date format

        if not store_files:
            raise FileNotFoundError(f"No processed data file found for store '{store_name}'.")

        # Return the path of the file with the most recent date
        store_files.sort(key=lambda x: x[0], reverse=True)
        return store_files[0][1]

    def _load_products_from_file(self, file_path):
        """Loads the list of products from a processed JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('products', [])
