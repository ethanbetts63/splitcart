def clean_raw_data_woolworths(raw_product_list: list) -> list:
    """
    Takes a list of raw product dictionaries from the Woolworths API and
    returns a new list containing only the essential, cleaned data for each product.

    Args:
        raw_product_list: A list of raw product dictionaries.

    Returns:
        A list of cleaned product dictionaries.
    """
    if not raw_product_list:
        return []

    cleaned_products = []
    for product in raw_product_list:
        clean_product = {
            'name': product.get('Name'),
            'brand': product.get('Brand'),
            'barcode': product.get('Barcode'),
            'stockcode': product.get('Stockcode'),
            'package_size': product.get('PackageSize'),
            'price': product.get('Price'),
            'was_price': product.get('WasPrice'),
            'is_on_special': product.get('IsOnSpecial'),
            'is_available': product.get('IsAvailable'),
            'unit_price': product.get('CupPrice'),
            'unit_of_measure': product.get('CupMeasure'),
            'url_friendly_name': product.get('UrlFriendlyName')
        }
        cleaned_products.append(clean_product)
        
    return cleaned_products
