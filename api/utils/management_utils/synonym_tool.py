import csv
import os
import importlib.util

# The new canonical path for the synonyms file
SYNONYM_FILE_PATH = 'api/data/analysis/brand_synonyms.py'
MATCH_FILE_PATH = 'brand_matches.csv'

def _get_synonyms_module():
    """Dynamically loads the synonyms module from the file path."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(SYNONYM_FILE_PATH), exist_ok=True)
    # Ensure the file exists
    if not os.path.exists(SYNONYM_FILE_PATH):
        with open(SYNONYM_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write("# This file contains the mapping of brand variations to a canonical brand name.\n")
            f.write("# It is generated and used by the 'create_synonyms' and normalization utilities.\n\n")
            f.write("BRAND_SYNONYMS = {\n}\n")

    spec = importlib.util.spec_from_file_location("brand_synonyms", SYNONYM_FILE_PATH)
    brand_synonyms_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(brand_synonyms_module)
    return brand_synonyms_module

def load_existing_synonyms():
    """
    Loads the BRAND_SYNONYMS dictionary from the specified file.
    Returns the dictionary and a set of all processed brands.
    """
    brand_synonyms_module = _get_synonyms_module()
    
    BRAND_SYNONYMS = getattr(brand_synonyms_module, 'BRAND_SYNONYMS', {})
    
    processed_brands = set(BRAND_SYNONYMS.keys())
    processed_brands.update(BRAND_SYNONYMS.values())
    return BRAND_SYNONYMS, processed_brands

def read_brand_matches():
    """Reads the brand_matches.csv file and returns its content."""
    if not os.path.exists(MATCH_FILE_PATH):
        return []
    with open(MATCH_FILE_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # Skip header
        return list(reader)

def append_synonym(synonym, canonical):
    """
    Appends a new synonym mapping to the brand_synonyms.py file.
    """
    with open(SYNONYM_FILE_PATH, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        
        for i, line in reversed(list(enumerate(lines))):
            if '}' in line:
                closing_brace_line_index = i
                break
        else:
            return False

        synonym_escaped = synonym.replace('"', '\\"')
        canonical_escaped = canonical.replace('"', '\\"')
        new_line = f'    "{synonym_escaped}": "{canonical_escaped}",\n'
        
        lines.insert(closing_brace_line_index, new_line)
        
        f.seek(0)
        f.writelines(lines)
        f.truncate()
    return True