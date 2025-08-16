import os
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from datetime import datetime

class Command(BaseCommand):
    help = 'Compares product prices and availability between two stores, category by category, from the latest available date.'

    def add_arguments(self, parser):
        parser.add_argument('company_name', type=str, help='The company to compare (e.g., woolworths, aldi, iga).')
        parser.add_argument('store_a_name', type=str, help='The name of the first store.')
        parser.add_argument('store_b_name', type=str, help='The name of the second store.')

    def handle(self, *args, **options):
        company_name = options['company_name'].lower()
        store_a_name = options['store_a_name']
        store_b_name = options['store_b_name']

        product_id_key = self._get_product_id_key(company_name)
        if not product_id_key:
            self.stdout.write(self.style.ERROR(f"Company '{company_name}' is not supported. Supported: woolworths, aldi, iga."))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Comparing {company_name.title()} Stores: '{store_a_name}' vs '{store_b_name}' ---"))

        base_path = os.path.join('api', 'data', 'processed_data', company_name)

        try:
            latest_date_dir_a = self._find_latest_date_dir(base_path, company_name, store_a_name)
            latest_date_dir_b = self._find_latest_date_dir(base_path, company_name, store_b_name)
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            return

        self.stdout.write(f"Found latest data for '{store_a_name}' in: {os.path.relpath(latest_date_dir_a)}")
        self.stdout.write(f"Found latest data for '{store_b_name}' in: {os.path.relpath(latest_date_dir_b)}")

        categories_a = self._get_category_files(latest_date_dir_a)
        categories_b = self._get_category_files(latest_date_dir_b)

        category_names_a = set(categories_a.keys())
        category_names_b = set(categories_b.keys())

        common_categories = sorted(list(category_names_a.intersection(category_names_b)))
        exclusive_to_a = sorted(list(category_names_a - category_names_b))
        exclusive_to_b = sorted(list(category_names_b - category_names_a))

        self.stdout.write(self.style.SUCCESS("\n--- Category Comparison Summary ---"))
        self.stdout.write(f"Common categories found: {len(common_categories)}")
        self.stdout.write(f"Exclusive to '{store_a_name}': {len(exclusive_to_a)}")
        self.stdout.write(f"Exclusive to '{store_b_name}': {len(exclusive_to_b)}")

        for category in common_categories:
            self.stdout.write(self.style.SUCCESS(f"\n--- Comparing Category: {category.upper()} ---"))
            
            products_a = self._load_products_from_file(categories_a[category])
            products_b = self._load_products_from_file(categories_b[category])

            products_a_by_sku = {p[product_id_key]: p for p in products_a if product_id_key in p and p.get(product_id_key)}
            products_b_by_sku = {p[product_id_key]: p for p in products_b if product_id_key in p and p.get(product_id_key)}

            skus_a = set(products_a_by_sku.keys())
            skus_b = set(products_b_by_sku.keys())

            common_skus = skus_a.intersection(skus_b)
            price_differences = []
            for sku in common_skus:
                prod_a = products_a_by_sku[sku]
                prod_b = products_b_by_sku[sku]
                if prod_a.get('price') != prod_b.get('price'):
                    price_differences.append({
                        'name': prod_a.get('name', 'N/A'),
                        'price_a': prod_a.get('price'),
                        'price_b': prod_b.get('price')
                    })
            
            self.stdout.write(f"  Products in '{store_a_name}': {len(skus_a)}")
            self.stdout.write(f"  Products in '{store_b_name}': {len(skus_b)}")
            self.stdout.write(f"  Common products: {len(common_skus)}")
            self.stdout.write(f"  Price differences: {len(price_differences)}")

            if price_differences:
                self.stdout.write(self.style.WARNING("  Products with Price Differences:"))
                for diff in price_differences[:5]:
                    price_a_str = f"${diff['price_a']:.2f}" if isinstance(diff['price_a'], (int, float)) else "[N/A]"
                    price_b_str = f"${diff['price_b']:.2f}" if isinstance(diff['price_b'], (int, float)) else "[N/A]"
                    self.stdout.write(f"    - {diff['name']}: '{store_a_name}' {price_a_str} vs '{store_b_name}' {price_b_str}")

        if exclusive_to_a:
            self.stdout.write(self.style.SUCCESS(f"\n--- Categories Exclusive to '{store_a_name}' ---"))
            for category in exclusive_to_a:
                try:
                    products = self._load_products_from_file(categories_a[category])
                    self.stdout.write(f"  - {category} ({len(products)} products)")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  - Could not load category {category}: {e}"))

        if exclusive_to_b:
            self.stdout.write(self.style.SUCCESS(f"\n--- Categories Exclusive to '{store_b_name}' ---"))
            for category in exclusive_to_b:
                try:
                    products = self._load_products_from_file(categories_b[category])
                    self.stdout.write(f"  - {category} ({len(products)} products)")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  - Could not load category {category}: {e}"))

    def _get_product_id_key(self, company_name):
        """Returns the unique product identifier key for a given company."""
        # All processed data seems to standardize on 'stockcode'
        id_keys = {
            'woolworths': 'stockcode',
            'aldi': 'stockcode',
            'iga': 'stockcode'
        }
        return id_keys.get(company_name)

    def _find_latest_date_dir(self, base_path, company_name, store_name):
        """Finds the most recent date-stamped subdirectory for a given store."""
        clean_store_name = slugify(store_name.lower().replace(company_name, '').strip())
        store_dir_path = os.path.join(base_path, clean_store_name)

        if not os.path.isdir(store_dir_path):
            raise FileNotFoundError(f"Directory for store '{store_name}' not found at '{store_dir_path}'")

        date_dirs = [d for d in os.listdir(store_dir_path) if os.path.isdir(os.path.join(store_dir_path, d))]
        
        valid_date_dirs = []
        for d in date_dirs:
            try:
                datetime.strptime(d, '%Y-%m-%d')
                valid_date_dirs.append(d)
            except ValueError:
                continue

        if not valid_date_dirs:
            raise FileNotFoundError(f"No valid date directories found in '{store_dir_path}'")

        latest_date = sorted(valid_date_dirs, reverse=True)[0]
        return os.path.join(store_dir_path, latest_date)

    def _get_category_files(self, date_dir_path):
        """Returns a dictionary of category_name: file_path for a given date directory."""
        category_files = {}
        for filename in os.listdir(date_dir_path):
            if filename.endswith('.json'):
                category_name = filename.replace('.json', '')
                category_files[category_name] = os.path.join(date_dir_path, filename)
        return category_files

    def _load_products_from_file(self, file_path):
        """Loads the list of products from a processed JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('products', [])
