from api.utils.normalization_utils.get_cleaned_name import get_cleaned_name
from api.utils.normalization_utils.clean_value import clean_value
from api.utils.normalization_utils.standardize_sizes_for_norm_string import standardize_sizes_for_norm_string
from api.data.analysis.brand_synonyms import BRAND_SYNONYMS

def get_normalized_string(product, extracted_sizes) -> str:
    """
    Takes a product object (or dictionary) and a list of extracted sizes,
    and returns the normalized_name_brand_size string.
    """
    # Safely get name and brand
    name = getattr(product, 'name', product.get('name', '')) if hasattr(product, 'get') else getattr(product, 'name', '')
    brand = getattr(product, 'brand', product.get('brand', '')) if hasattr(product, 'get') else getattr(product, 'brand', '')

    # Ensure name and brand are strings
    name = str(name) if name is not None else ''
    brand = str(brand) if brand is not None else ''

    # Apply brand synonym mapping
    # The brand is cleaned (lowercase, no punctuation) before lookup
    cleaned_brand_for_lookup = clean_value(brand) # Using clean_value for consistency
    brand = BRAND_SYNONYMS.get(cleaned_brand_for_lookup, brand)

    # Calculate cleaned name
    cleaned_name = get_cleaned_name(name, brand, extracted_sizes)

    # Standardize sizes for the normalization string
    standardized_sizes = standardize_sizes_for_norm_string(extracted_sizes)

    # Generate normalized_name_brand_size
    normalized_string = clean_value(cleaned_name) + \
                        clean_value(brand) + \
                        clean_value(" ".join(standardized_sizes) if standardized_sizes else "")
    
    return normalized_string
