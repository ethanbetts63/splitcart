from api.utils.processing_utils import _create_coles_url_slug
from datetime import datetime

def clean_raw_data_coles(raw_product_list: list, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Coles product data and wraps it in a dictionary
    containing metadata about the scrape.
    """
    cleaned_products = []
    if raw_product_list:
        for product in raw_product_list:
            if not product or product.get('_type') != 'PRODUCT':
                continue

            pricing = product.get('pricing', {}) or {}
            unit_info = pricing.get('unit', {}) or {}
            online_heirs = product.get('onlineHeirs', [{}])[0]

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
                'url': product_url,
                'departments': [{'name': online_heirs.get('subCategory'), 'id': online_heirs.get('subCategoryId')}],
                'categories': [{'name': online_heirs.get('category'), 'id': online_heirs.get('categoryId')}],
                'subcategories': [{'name': online_heirs.get('aisle'), 'id': online_heirs.get('aisleId')}]
            }
            cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "store": "coles",
            "category": category,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
