import json
import os
from datetime import datetime
from .category_parser import get_category_path

def data_combiner(page_files):
    """
    Combines product data from multiple JSON files (pages) into a single list.
    It also extracts metadata and adds a consistent category_path to each product.
    """
    combined_products = []
    metadata = {}
    company_name = ""

    if not page_files:
        return combined_products, metadata

    page_files.sort()

    try:
        # Use the first file to determine company and extract metadata
        filename = os.path.basename(page_files[0])
        company_name = filename.split('_')[0]
        with open(page_files[0], 'r', encoding='utf-8') as f:
            # Some raw files are lists, some are dicts with metadata
            raw_data = json.load(f)
            if isinstance(raw_data, dict) and 'metadata' in raw_data:
                metadata = raw_data.get('metadata', {})
            else:
                metadata = {'company': company_name, 'scraped_at': datetime.now().isoformat()}
    except (json.JSONDecodeError, FileNotFoundError, IndexError) as e:
        print(f"Error reading metadata from {page_files[0]}: {e}")
        return [], {}

    # Process all files for their product lists
    for file_path in page_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Find the list of products, whether it's the root object or under a key
                products = data.get('products', []) if isinstance(data, dict) else data
                if not isinstance(products, list):
                    continue

                for product in products:
                    # If category_path is missing or empty, try to generate it
                    if not product.get('category_path'):
                        product['category_path'] = get_category_path(product, company_name)
                    combined_products.append(product)

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error processing file {file_path}: {e}")
            continue
            
    return combined_products, metadata