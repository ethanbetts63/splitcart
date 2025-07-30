from datetime import datetime

def clean_raw_data_woolworths(raw_product_list: list, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Woolworths product data and wraps it in a dictionary
    containing metadata about the scrape.

    Args:
        raw_product_list: A list of raw product dictionaries.
        category: The category slug being scraped (e.g., 'electronics').
        page_num: The page number of the data.
        timestamp: The datetime object of when the scrape occurred.

    Returns:
        A dictionary containing metadata and the cleaned list of products.
    """
    cleaned_products = []
    if raw_product_list:
        for product in raw_product_list:
            stockcode = product.get('Stockcode')
            url_slug = product.get('UrlFriendlyName')
            product_url = None
            if stockcode and url_slug:
                product_url = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{url_slug}"

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
                'url': product_url 
            }
            cleaned_products.append(clean_product)
    
    data_packet = {
        "metadata": {
            "store": "woolworths",
            "category": category,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
    
    return data_packet
