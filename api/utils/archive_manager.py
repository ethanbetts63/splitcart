import os
import json
from datetime import datetime

def archive_manager(processed_data_path: str, store_name: str, scrape_date: str, category_name: str, combined_products: list, source_files: list) -> bool:
    """
    Creates a data packet with metadata and saves the combined list of products
    to the structured processed_data directory.

    Args:
        processed_data_path: The root path for the processed_data directory.
        store_name: The name of the store (e.g., 'coles').
        scrape_date: The date of the scrape (e.g., '2025-07-30').
        category_name: The name of the category (e.g., 'fruit-vegetables').
        combined_products: The final, combined list of product dictionaries.
        source_files: The list of raw file paths that were combined.

    Returns:
        True if the file was saved successfully, False otherwise.
    """
    if not combined_products:
        print(f"Warning: Received an empty product list for {store_name}/{category_name}. Nothing to archive.")
        return False

    try:
        # --- 1. Create the final data packet with metadata ---
        archive_packet = {
            "metadata": {
                "store": store_name,
                "category": category_name,
                "scrape_date": scrape_date,
                "product_count": len(combined_products),
                "source_files": [os.path.basename(f) for f in source_files]
            },
            "products": combined_products
        }

        # --- 2. Construct the target directory path ---
        target_dir = os.path.join(processed_data_path, store_name, scrape_date)
        os.makedirs(target_dir, exist_ok=True)
        
        # --- 3. Define and save the final output file ---
        output_filename = f"{category_name}.json"
        output_filepath = os.path.join(target_dir, output_filename)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(archive_packet, f, indent=4)
        
        print(f"Successfully archived {len(combined_products)} products to {output_filepath}")
        return True

    except IOError as e:
        print(f"ERROR: Could not save archive file for {category_name}. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in the archive manager: {e}")
        return False
