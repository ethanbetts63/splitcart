import os
import json

def archive_manager(processed_data_path: str, company_name: str, state: str, store_name: str, scrape_date: str, category_name: str, combined_products: list, source_files: list) -> bool:
    """
    Creates a data packet with the new metadata structure and saves the combined
    list of products to the structured processed_data directory.

    Args:
        processed_data_path: The root path for the processed_data directory.
        company_name: The name of the company (e.g., 'coles').
        state: The state of the store (e.g., 'NSW').
        store_name: The name of the specific store (e.g., 'national', 'Dianella').
        scrape_date: The date of the scrape (e.g., '2025-08-03').
        category_name: The name of the category (e.g., 'fruit-vegetables').
        combined_products: The final, combined list of product dictionaries.
        source_files: The list of raw file paths that were combined.

    Returns:
        True if the file was saved successfully, False otherwise.
    """
    if not combined_products:
        print(f"Warning: Received an empty product list for {company_name}/{state}/{store_name}/{category_name}. Nothing to archive.")
        return False

    try:
        # Create the final data packet with the new metadata format
        archive_packet = {
            "metadata": {
                "company": company_name,
                "state": state,
                "store": store_name,
                "category": category_name,
                "scrape_date": scrape_date,
                "product_count": len(combined_products),
                "source_files": [os.path.basename(f) for f in source_files]
            },
            "products": combined_products
        }

        # Construct the new target directory path: processed_data/company/state/store/date/
        target_dir = os.path.join(processed_data_path, company_name, state, store_name, scrape_date)
        os.makedirs(target_dir, exist_ok=True)
        
        output_filename = f"{category_name.replace('/', '_')}.json"
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
