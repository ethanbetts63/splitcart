
import json
import os

def read_generated_synonyms():
    """
    Reads the generated brand synonyms from the JSON file and returns them as a list of tuples.
    """
    path = 'api/data/analysis/generated_brand_synonyms.json'
    if not os.path.exists(path):
        return []
    
    with open(path, 'r') as f:
        try:
            synonyms_dict = json.load(f)
        except json.JSONDecodeError:
            return []
            
    # Convert the dictionary to a list of tuples
    return list(synonyms_dict.items())
