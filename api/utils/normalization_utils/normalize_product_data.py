from .extract_sizes import extract_sizes
from .get_cleaned_name import get_cleaned_name
from .clean_value import clean_value

def normalize_product_data(product) -> str:
    """
    Takes a product object (model instance or dictionary), extracts and cleans sizes,
    cleans the name, and returns a normalized_name_brand_size string.
    """
    # Safely get name, brand, and sizes, handling both object attributes and dictionary keys
    name = getattr(product, 'name', product.get('name', '')) if hasattr(product, 'get') else getattr(product, 'name', '')
    brand = getattr(product, 'brand', product.get('brand', '')) if hasattr(product, 'get') else getattr(product, 'brand', '')
    existing_sizes = getattr(product, 'sizes', product.get('sizes', [])) if hasattr(product, 'get') else getattr(product, 'sizes', [])

    # Ensure name and brand are strings
    name = str(name) if name is not None else ''
    brand = str(brand) if brand is not None else ''

    # Extract sizes from name and brand
    name_sizes = extract_sizes(name)
    brand_sizes = extract_sizes(brand)

    # Combine with existing sizes, ensure uniqueness, and sort
    all_sizes = set(existing_sizes)
    all_sizes.update(name_sizes)
    all_sizes.update(brand_sizes)
    
    extracted_sizes = sorted(list(all_sizes))

    # Calculate cleaned name
    cleaned_name = get_cleaned_name(name, brand, extracted_sizes)

    # Generate normalized_name_brand_size
    normalized_string = clean_value(cleaned_name) + \
                        clean_value(brand) + \
                        clean_value(" ".join(extracted_sizes) if extracted_sizes else "")
    
    return normalized_string