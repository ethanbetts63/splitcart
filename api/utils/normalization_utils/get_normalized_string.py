from .get_cleaned_name import get_cleaned_name
from .clean_value import clean_value

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

    # Calculate cleaned name
    cleaned_name = get_cleaned_name(name, brand, extracted_sizes)

    # Generate normalized_name_brand_size
    normalized_string = clean_value(cleaned_name) + \
                        clean_value(brand) + \
                        clean_value(" ".join(extracted_sizes) if extracted_sizes else "")
    
    return normalized_string
