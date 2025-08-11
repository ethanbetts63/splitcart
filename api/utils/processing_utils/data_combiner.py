import json
from typing import Tuple, List, Dict, Any

def data_combiner(file_paths: list) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Takes a list of file paths to raw data JSON files, opens each one,
    extracts the 'products' list, and combines them into a single list.
    It also extracts the metadata from the first file in the list.

    Args:
        file_paths: A list of absolute paths to the JSON files for each page
                    of a category scrape.

    Returns:
        A tuple containing:
        - A single list of all product dictionaries.
        - A dictionary containing the metadata from the first file.
        Returns ([], {}) if an error occurs or no files are provided.
    """
    if not file_paths:
        return [], {}

    all_products = []
    metadata = {}
    
    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_packet = json.load(f)
                
                # On the first file, grab the metadata
                if i == 0:
                    metadata = data_packet.get('metadata', {})

                products_on_page = data_packet.get('products')
                
                if isinstance(products_on_page, list):
                    all_products.extend(products_on_page)
                else:
                    print(f"Warning: 'products' key was not a list in file: {file_path}")

        except FileNotFoundError:
            print(f"Error: File not found at path: {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: Could not read or parse {file_path}. Details: {e}")
            continue
            
    return all_products, metadata
