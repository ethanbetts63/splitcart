from .create_coles_url_slug import _create_coles_url_slug
from datetime import datetime


def clean_raw_data_coles(raw_product_list: list, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Coles product data and wraps it in a dictionary
    containing metadata about the scrape.

    Args:
        raw_product_list: A list of raw dictionaries from the 'results' key.
        category: The category slug being scraped (e.g., 'fruit-vegetables').
        page_num: The page number of the data.
        timestamp: The datetime object of when the scrape occurred.

    Returns:
        A dictionary containing metadata and the cleaned list of products.
    """
    cleaned_products = []
    if raw_product_list:
        for product in raw_product_list:
            if not product or product.get('_type') != 'PRODUCT':
                continue

            pricing = product.get('pricing', {}) or {}
            unit_info = pricing.get('unit', {}) or {}
            
            product_id = product.get('id')
            product_name = product.get('name')
            product_size = product.get('size')

            product_url = None
            if product_id and product_name and product_size:
                slug = _create_coles_url_slug(product_name, product_size)
                product_url = f"https://www.coles.com.au/product/{slug}-{product_id}"

            unit_measure_qty = unit_info.get('ofMeasureQuantity', '')
            unit_measure_units = unit_info.get('ofMeasureUnits', '')
            unit_of_measure = f"{unit_measure_qty}{unit_measure_units}".lower() if unit_measure_qty and unit_measure_units else None

            clean_product = {
                'name': product_name,
                'brand': product.get('brand'),
                'barcode': None,
                'stockcode': product_id,
                'package_size': product_size,
                'price': pricing.get('now'),
                'was_price': pricing.get('was') if pricing.get('was') != 0 else None,
                'is_on_special': pricing.get('onlineSpecial', False),
                'is_available': product.get('availability', False),
                'unit_price': unit_info.get('price'),
                'unit_of_measure': unit_of_measure,
                'url': product_url
            }
            cleaned_products.append(clean_product)
    
    data_packet = {
        "metadata": {
            "store": "coles",
            "category": category,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
    
    return data_packet
