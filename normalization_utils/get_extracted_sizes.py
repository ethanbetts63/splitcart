from api.utils.normalization_utils.extract_sizes import extract_sizes

def get_extracted_sizes(product) -> list:
    """
    Takes a product object (model instance or dictionary) and returns a sorted list of unique sizes.
    """
    # Safely get name, brand, and sizes, handling both object attributes and dictionary keys
    name = getattr(product, 'name', product.get('name', '')) if hasattr(product, 'get') else getattr(product, 'name', '')
    brand = getattr(product, 'brand', product.get('brand', '')) if hasattr(product, 'get') else getattr(product, 'brand', '')
    package_size = getattr(product, 'package_size', product.get('package_size', '')) if hasattr(product, 'get') else getattr(product, 'package_size', '')
    existing_sizes = getattr(product, 'sizes', product.get('sizes', [])) if hasattr(product, 'get') else getattr(product, 'sizes', [])

    # Ensure name and brand are strings
    name = str(name) if name is not None else ''
    brand = str(brand) if brand is not None else ''
    package_size = str(package_size) if package_size is not None else ''

    # Extract sizes from name and brand
    name_sizes = extract_sizes(name)
    brand_sizes = extract_sizes(brand)
    package_size_sizes = extract_sizes(package_size)

    # Combine with existing sizes, ensure uniqueness, and sort
    all_sizes = set(existing_sizes)
    all_sizes.update(name_sizes)
    all_sizes.update(brand_sizes)
    all_sizes.update(package_size_sizes)
    
    return sorted(list(all_sizes))
