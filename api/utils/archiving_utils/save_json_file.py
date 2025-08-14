import os
import json
from django.conf import settings

def save_json_file(company_slug, store_id, data_dict):
    """
    Saves a dictionary as a JSON file in the appropriate archive directory.

    Args:
        company_slug (str): The slug of the company (for the directory).
        store_id (str): The ID of the store (for the filename).
        data_dict (dict): The data to be saved as JSON.

    Returns:
        str: The path to the saved file.
    """
    # Construct the directory path relative to the Django project's BASE_DIR
    directory_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'store_data', company_slug)

    # Create the directory if it doesn't exist
    os.makedirs(directory_path, exist_ok=True)

    # Construct the full file path
    file_path = os.path.join(directory_path, f"{store_id}.json")

    # Write the data to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, indent=4)

    return file_path
