
import json
import os

AUTO_SYNONYMS_FILE_PATH = 'api/data/analysis/generated_brand_synonyms.json'

def save_synonym(new_synonym):
    """
    Saves a new synonym to the auto-generated synonyms JSON file.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(AUTO_SYNONYMS_FILE_PATH), exist_ok=True)

    # Load existing auto-generated synonyms
    try:
        with open(AUTO_SYNONYMS_FILE_PATH, 'r') as f:
            auto_synonyms = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        auto_synonyms = {}

    # Add the new synonym and write back to the file
    auto_synonyms.update(new_synonym)
    with open(AUTO_SYNONYMS_FILE_PATH, 'w') as f:
        json.dump(auto_synonyms, f, indent=4)

