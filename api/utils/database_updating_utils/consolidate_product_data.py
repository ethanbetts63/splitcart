import os
import json
from collections import defaultdict

def consolidate_product_data(archive_dir: str):
    """
    Pass 1: Read all JSON files and consolidate product data in memory.
    """
    print("--- Pass 1: Consolidating product data from JSON files ---")
    consolidated_data = defaultdict(lambda: {
        'price_history': [],
        'category_paths': set(),
        'product_details': {},
        'company_name': None
    })

    if not os.path.exists(archive_dir):
        print(f"Archive directory not found: {archive_dir}")
        return {}

    company_folders = [f for f in os.scandir(archive_dir) if f.is_dir()]
    for company_folder in company_folders:
        store_files = [f for f in os.scandir(company_folder.path) if f.name.endswith('.json')]
        
        for store_file in store_files:
            with open(store_file.path, 'r') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            store_id = metadata.get('store_id')
            company_name = metadata.get('company_name')
            if not store_id or not company_name:
                continue

            for product_data in data.get('products', []):
                name_str = product_data.get('name', '').strip()
                brand_str = product_data.get('brand', '').strip()
                size_str = product_data.get('size', '').strip()

                if not name_str:
                    continue

                composite_key = (name_str.lower(), brand_str.lower(), size_str.lower())

                for price_entry in product_data.get('price_history', []):
                    price_entry['store_id'] = store_id
                    consolidated_data[composite_key]['price_history'].append(price_entry)

                for path in product_data.get('category_paths', []):
                    consolidated_data[composite_key]['category_paths'].add(tuple(path))

                if not consolidated_data[composite_key]['product_details']:
                    consolidated_data[composite_key]['product_details'] = product_data
                
                if not consolidated_data[composite_key]['company_name']:
                    consolidated_data[composite_key]['company_name'] = company_name

    print(f"Consolidated data for {len(consolidated_data)} unique products.")
    return consolidated_data
