import json
import os

VARIATIONS_FILE_PATH = 'api/data/analysis/generated_name_variations.json'

def save_name_variation(new_variation):
    """
    Appends a new product name variation to the JSON file.
    """
    os.makedirs(os.path.dirname(VARIATIONS_FILE_PATH), exist_ok=True)

    try:
        with open(VARIATIONS_FILE_PATH, 'r') as f:
            variations = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        variations = []

    variations.append(new_variation)

    with open(VARIATIONS_FILE_PATH, 'w') as f:
        json.dump(variations, f, indent=4)
