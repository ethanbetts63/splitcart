import csv
import os
import importlib.util

# File paths
SYNONYM_FILE_PATH = 'api/data/analysis/brand_synonyms.py'
NON_MATCH_FILE_PATH = 'api/data/analysis/brand_non_matches.csv'
UNSURE_MATCH_FILE_PATH = 'api/data/analysis/brand_unsure_matches.csv'
MATCH_FILE_PATH = 'brand_matches.csv'

def _get_synonyms_module():
    """Dynamically loads the synonyms module from the file path."""
    os.makedirs(os.path.dirname(SYNONYM_FILE_PATH), exist_ok=True)
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
    """Loads the BRAND_SYNONYMS dictionary and returns a set of all processed brands."""
    brand_synonyms_module = _get_synonyms_module()
    BRAND_SYNONYMS = getattr(brand_synonyms_module, 'BRAND_SYNONYMS', {})
    processed_brands = set(BRAND_SYNONYMS.keys())
    processed_brands.update(BRAND_SYNONYMS.values())
    return processed_brands

def _load_csv_to_set(filepath):
    """Generic function to load a 2-column CSV into a set of sorted tuples."""
    if not os.path.exists(filepath):
        return set()
    
    data_set = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                data_set.add(tuple(sorted((row[0], row[1]))))
    return data_set

def load_non_matches():
    """Loads the non-match history into a set for fast lookups."""
    return _load_csv_to_set(NON_MATCH_FILE_PATH)

def load_unsure_matches():
    """Loads the unsure-match history into a set for fast lookups."""
    return _load_csv_to_set(UNSURE_MATCH_FILE_PATH)

def read_brand_matches():
    """Reads the brand_matches.csv file and returns its content."""
    if not os.path.exists(MATCH_FILE_PATH):
        return []
    with open(MATCH_FILE_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # Skip header
        return list(reader)

def append_synonym(synonym, canonical):
    """Appends a new synonym mapping to the brand_synonyms.py file."""
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

def _append_to_csv(filepath, brand1, brand2):
    """Generic function to append a brand pair to a CSV file."""
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([brand1, brand2])
    return True

def append_non_match(brand1, brand2):
    """Appends a pair of non-matching brands to the history file."""
    return _append_to_csv(NON_MATCH_FILE_PATH, brand1, brand2)

def append_unsure_match(brand1, brand2):
    """Appends a pair of unsure brands to the history file."""
    return _append_to_csv(UNSURE_MATCH_FILE_PATH, brand1, brand2)

