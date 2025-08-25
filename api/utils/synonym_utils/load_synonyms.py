import json
import importlib.util
import sys

def load_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def load_synonyms():
    """
    Loads both manual and auto-generated brand synonyms.
    """
    # Load BRAND_SYNONYMS from brand_synonyms.py at the project root
    try:
        brand_synonyms_module = load_module_from_file('brand_synonyms.py', 'brand_synonyms')
        all_synonyms = brand_synonyms_module.BRAND_SYNONYMS.copy()
    except FileNotFoundError:
        all_synonyms = {}

    # Try to load auto-generated synonyms and merge them
    try:
        with open('api/data/analysis/generated_brand_synonyms.json', 'r') as f:
            auto_synonyms = json.load(f)
            all_synonyms.update(auto_synonyms)
    except FileNotFoundError:
        # It's okay if the file doesn't exist yet
        pass
    except json.JSONDecodeError:
        # Handle cases where the file is empty or malformed
        pass

    return all_synonyms