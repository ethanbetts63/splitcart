import json
import os

AUTO_SYNONYMS_FILE_PATH = 'api/data/analysis/generated_brand_synonyms.json'

def bulk_save_synonyms(new_synonyms: dict):
    """
    Saves a dictionary of new synonyms to the auto-generated synonyms JSON file
    in a single batch operation.
    """
    if not new_synonyms:
        return

    # Ensure the directory exists
    os.makedirs(os.path.dirname(AUTO_SYNONYMS_FILE_PATH), exist_ok=True)

    # Load existing auto-generated synonyms
    try:
        with open(AUTO_SYNONYMS_FILE_PATH, 'r') as f:
            auto_synonyms = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        auto_synonyms = {}

    # Add the new synonyms and write back to the file
    auto_synonyms.update(new_synonyms)
    with open(AUTO_SYNONYMS_FILE_PATH, 'w') as f:
        json.dump(auto_synonyms, f, indent=4)
