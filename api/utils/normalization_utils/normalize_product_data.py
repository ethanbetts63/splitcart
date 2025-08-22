from .extract_sizes import extract_sizes
from .get_cleaned_name import get_cleaned_name
from .clean_value import clean_value

def normalize_product_data(product_data: dict) -> dict:
    """
    Takes a product data dictionary, extracts and cleans sizes, 
    cleans the name, and adds a normalized_name_brand_size key.
    """
    name = product_data.get('name', '')
    brand = product_data.get('brand', '')
    
    # Extract sizes from name and brand
    name_sizes = extract_sizes(name)
    brand_sizes = extract_sizes(brand)

    # Combine with existing sizes from the 'size' field, ensure uniqueness, and sort
    existing_sizes = extract_sizes(product_data.get('size', ''))
    all_sizes = set(existing_sizes)
    all_sizes.update(name_sizes)
    all_sizes.update(brand_sizes)
    
    # Add the cleaned sizes to the product data
    product_data['extracted_sizes'] = sorted(list(all_sizes))

    # Calculate cleaned name
    cleaned_name = get_cleaned_name(name, brand, product_data['extracted_sizes'])

    # Generate normalized_name_brand_size
    normalized_string = clean_value(cleaned_name) + \
                        clean_value(brand) + \
                        clean_value(" ".join(product_data['extracted_sizes']) if product_data['extracted_sizes'] else "")
    
    product_data['normalized_name_brand_size'] = normalized_string
    
    return product_data
