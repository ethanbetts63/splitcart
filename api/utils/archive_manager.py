import os
import json
from datetime import datetime

def archive_manager(processed_data_path: str, store_name: str, scrape_date: str, category_name: str, combined_products: list) -> bool:
    """
    Saves a combined list of products to the structured processed_data
    directory, creating subdirectories as needed.

    Args:
        processed_data_path: The root path for the processed_data directory.
        store_name: The name of the store (e.g., 'coles').
        scrape_date: The date of the scrape (e.g., '2025-07-30').
        category_name: The name of the category (e.g., 'fruit-vegetables').
        combined_products: The final, combined list of product dictionaries.

    Returns:
        True if the file was saved successfully, False otherwise.
    """
    if not combined_products:
        print(f"Warning: Received an empty product list for {store_name}/{category_name}. Nothing to archive.")
        return False

    try:
        # --- 1. Construct the target directory path ---
        # e.g., /path/to/processed_data/coles/2025-07-30/
        target_dir = os.path.join(processed_data_path, store_name, scrape_date)

        # --- 2. Create the directories if they don't exist ---
        os.makedirs(target_dir, exist_ok=True)
        
        # --- 3. Define the final output file path ---
        output_filename = f"{category_name}.json"
        output_filepath = os.path.join(target_dir, output_filename)
        
        # --- 4. Save the combined data as a new JSON file ---
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(combined_products, f, indent=4)
        
        print(f"Successfully archived {len(combined_products)} products to {output_filepath}")
        return True

    except IOError as e:
        print(f"ERROR: Could not save archive file for {category_name}. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in the archive manager: {e}")
        return False
