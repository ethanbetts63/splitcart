import os
import json
from typing import Dict, Any

def archive_manager(processed_data_path: str, archive_packet: Dict[str, Any]) -> bool:
    """
    Saves a complete data packet (metadata and products) to the structured
    processed_data directory. The path is derived from the metadata.

    Args:
        processed_data_path: The root path for the processed_data directory.
        archive_packet: The final data packet containing 'metadata' and 'products'.

    Returns:
        True if the file was saved successfully, False otherwise.
    """
    metadata = archive_packet.get("metadata", {})
    products = archive_packet.get("products", [])

    if not products:
        print("Warning: Received an empty product list. Nothing to archive.")
        return False
    
    # Extract path components from metadata
    company_name = metadata.get("company")
    state = metadata.get("state")
    # Use store_id if available, otherwise fall back to store, then store_name
    store_identifier = metadata.get("store_id") or metadata.get("store") or metadata.get("store_name")
    scrape_date = metadata.get("scrape_date")
    category_name = metadata.get("category")

    if not all([company_name, state, store_identifier, scrape_date, category_name]):
        print(f"ERROR: Missing one or more required metadata fields for archiving.")
        return False

    try:
        # Construct the target directory path from metadata
        target_dir = os.path.join(processed_data_path, company_name, state, str(store_identifier), scrape_date)
        os.makedirs(target_dir, exist_ok=True)
        
        output_filename = f"{category_name.replace('/', '_')}.json"
        output_filepath = os.path.join(target_dir, output_filename)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(archive_packet, f, indent=4)
        
        print(f"Successfully archived {len(products)} products to {output_filepath}")
        return True

    except IOError as e:
        print(f"ERROR: Could not save archive file for {category_name}. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in the archive manager: {e}")
        return False
