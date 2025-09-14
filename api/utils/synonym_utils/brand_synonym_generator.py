import json
import os
from products.models import ProductBrand

GENERATED_SYNONYMS_PATH = 'api/data/analysis/generated_brand_synonyms.json'

def generate_brand_synonym_file(command):
    """
    Generates the brand synonym JSON file from scratch by reading all ProductBrand
    model instances from the database.
    """
    command.stdout.write("--- Regenerating brand synonym file from database ---")
    synonyms = {}

    # Query all brands that have variations
    all_brands = ProductBrand.objects.filter(name_variations__isnull=False)

    for brand in all_brands:
        canonical_name = brand.name
        for variation in brand.name_variations:
            if variation.lower() != canonical_name.lower():
                synonyms[variation] = canonical_name

    # Ensure the directory exists
    os.makedirs(os.path.dirname(GENERATED_SYNONYMS_PATH), exist_ok=True)

    # Overwrite the file with the newly generated synonyms
    try:
        with open(GENERATED_SYNONYMS_PATH, 'w', encoding='utf-8') as f:
            json.dump(synonyms, f, indent=4)
        command.stdout.write(command.style.SUCCESS(f"Successfully regenerated brand synonym file with {len(synonyms)} entries."))
    except IOError as e:
        command.stderr.write(command.style.ERROR(f"Could not write to brand synonym file: {e}"))
