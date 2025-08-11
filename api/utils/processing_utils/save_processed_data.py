import os
import json

def save_processed_data(processed_data_path, processed_data_packet):
    """
    Saves the combined data packet to a flat processed_data directory.
    The filename will be in the format: <store_id>_<scrape_date>.json.

    Args:
        processed_data_path (str): The base path to the processed_data directory.
        processed_data_packet (dict): The dictionary containing the combined metadata and products.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    try:
        metadata = processed_data_packet['metadata']
        # We need store_id and scrape_date for the filename
        store_id = metadata['store_id']
        scrape_date = metadata['scrape_date']

        # Create the filename
        processed_data_filename = f"{store_id}_{scrape_date}.json"
        processed_data_filepath = os.path.join(processed_data_path, processed_data_filename)

        # Ensure the base directory exists
        os.makedirs(processed_data_path, exist_ok=True)

        # Write the JSON data to the file
        with open(processed_data_filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_data_packet, f, indent=4)
        
        return True

    except KeyError as e:
        print(f"Error: Missing key in metadata for archiving: {e}")
        return False
    except Exception as e:
        print(f"An error occurred during archiving: {e}")
        return False