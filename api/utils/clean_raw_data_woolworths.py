import json
from datetime import datetime

def clean_raw_data_woolworths(raw_product_list: list, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Woolworths product data and wraps it in a dictionary
    containing metadata about the scrape.
    """
    cleaned_products = []
    if raw_product_list:
        for product in raw_product_list:
            additional_attributes = product.get('AdditionalAttributes', {})
            stockcode = product.get('Stockcode')
            url_slug = product.get('UrlFriendlyName')
            product_url = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{url_slug}" if stockcode and url_slug else None

            # Safely parse JSON strings, defaulting to empty lists if None or invalid
            try:
                departments = json.loads(additional_attributes.get('piesdepartmentnamesjson', '[]'))
            except (json.JSONDecodeError, TypeError):
                departments = []
            try:
                categories = json.loads(additional_attributes.get('piescategorynamesjson', '[]'))
            except (json.JSONDecodeError, TypeError):
                categories = []
            try:
                subcategories = json.loads(additional_attributes.get('piessubcategorynamesjson', '[]'))
            except (json.JSONDecodeError, TypeError):
                subcategories = []

            clean_product = {
                'name': product.get('Name'),
                'brand': product.get('Brand'),
                'barcode': product.get('Barcode'),
                'stockcode': stockcode,
                'package_size': product.get('PackageSize'),
                'price': product.get('Price'),
                'was_price': product.get('WasPrice'),
                'is_on_special': product.get('IsOnSpecial'),
                'is_available': product.get('IsAvailable'),
                'unit_price': product.get('CupPrice'),
                'unit_of_measure': product.get('CupMeasure'),
                'url': product_url,
                'departments': departments,
                'categories': categories,
                'subcategories': subcategories
            }
            cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "store": "woolworths",
            "category": category,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
