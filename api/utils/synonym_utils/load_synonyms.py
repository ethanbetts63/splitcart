
import json
from brand_synonyms import BRAND_SYNONYMS

def load_synonyms():
    """
    Loads both manual and auto-generated brand synonyms.
    """
    # Start with the manually curated synonyms
    all_synonyms = BRAND_SYNONYMS.copy()

    # Try to load auto-generated synonyms and merge them
    try:
        with open('api/data/analysis/auto_generated_brand_synonyms.json', 'r') as f:
            auto_synonyms = json.load(f)
            all_synonyms.update(auto_synonyms)
    except FileNotFoundError:
        # It's okay if the file doesn't exist yet
        pass
    except json.JSONDecodeError:
        # Handle cases where the file is empty or malformed
        pass

    return all_synonyms

