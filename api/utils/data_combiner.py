import json

def data_combiner(file_paths: list) -> list:
    """
    Takes a list of file paths to raw data JSON files, opens each one,
    extracts the 'products' list, and combines them into a single list.

    Args:
        file_paths: A list of absolute paths to the JSON files for each page
                    of a category scrape.

    Returns:
        A single list containing all product dictionaries from all pages,
        or an empty list if an error occurs or no products are found.
    """
    if not file_paths:
        return []

    all_products = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_packet = json.load(f)
                
                # Each file is a dictionary with a 'products' key
                products_on_page = data_packet.get('products')
                
                if isinstance(products_on_page, list):
                    all_products.extend(products_on_page)
                else:
                    print(f"Warning: 'products' key was not a list in file: {file_path}")

        except FileNotFoundError:
            print(f"Error: File not found at path: {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: Could not read or parse {file_path}. Details: {e}")
            # Decide if you want to stop processing or just skip the file.
            # For robustness, we'll just skip the corrupted file.
            continue
            
    return all_products
