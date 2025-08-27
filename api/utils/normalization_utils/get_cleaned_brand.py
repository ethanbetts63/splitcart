import json
import os
from api.data.analysis.brand_synonyms import BRAND_SYNONYMS
from .clean_value import clean_value

# Load brand rules once when the module is loaded
BRAND_RULES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'brand_rules.json')
BRAND_RULES = []
if os.path.exists(BRAND_RULES_PATH):
    with open(BRAND_RULES_PATH, 'r') as f:
        BRAND_RULES = json.load(f)

def get_cleaned_brand(brand, name):
    """
    Cleans a product brand using a synonym dictionary and a set of conditional rules.
    
    Args:
        brand (str): The original brand of the product.
        name (str): The original name of the product (used for conditional rules).
        
    Returns:
        str: The cleaned, canonical brand name.
    """
    if not brand:
        return ''

    # Ensure inputs are strings for consistent processing
    brand = str(brand)
    name = str(name).lower()

    # Step 1: Apply brand synonym mapping for direct replacements
    cleaned_brand_for_lookup = clean_value(brand)
    cleaned_brand = BRAND_SYNONYMS.get(cleaned_brand_for_lookup, brand)

    # Step 2: Apply conditional brand rules for more complex cases
    for rule in BRAND_RULES:
        rule_brands = [b.lower() for b in rule.get('brands', [])]
        condition_values = [v.lower() for v in rule.get('condition_values', [])]

        # Check if the current brand matches one of the rule's brands
        if cleaned_brand.lower() in rule_brands:
            # Check if the product name contains any of the condition keywords
            if any(keyword in name for keyword in condition_values):
                cleaned_brand = rule['canonical_brand']
                break # Stop after the first matching rule

    return cleaned_brand
