import os
import json

def archive_manager(processed_data_path, archive_packet):
    """
    Saves the combined data packet to a flat processed_data directory.
    The filename will be in the format: <store_id>_<scrape_date>.json.

    Args:
        processed_data_path (str): The base path to the processed_data directory.
        archive_packet (dict): The dictionary containing the combined metadata and products.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    try:
        metadata = archive_packet['metadata']
        # We need store_id and scrape_date for the filename
        store_id = metadata['store_id']
        scrape_date = metadata['scrape_date']

        # Create the filename
        archive_filename = f"{store_id}_{scrape_date}.json"
        archive_filepath = os.path.join(processed_data_path, archive_filename)

        # Ensure the base directory exists
        os.makedirs(processed_data_path, exist_ok=True)

        # Write the JSON data to the file
        with open(archive_filepath, 'w', encoding='utf-8') as f:
            json.dump(archive_packet, f, indent=4)
        
        return True

    except KeyError as e:
        print(f"Error: Missing key in metadata for archiving: {e}")
        return False
    except Exception as e:
        print(f"An error occurred during archiving: {e}")
        return False