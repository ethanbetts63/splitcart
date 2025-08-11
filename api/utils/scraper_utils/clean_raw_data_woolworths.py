import json
from datetime import datetime

def clean_raw_data_woolworths(raw_product_list: list, company: str, store_id: str, store_name: str, state: str, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Woolworths product data according to the V2 schema and
    wraps it in a dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    if not raw_product_list:
        raw_product_list = []

    for product in raw_product_list:
        if not product:
            continue

        attrs = product.get('AdditionalAttributes', {}) or {}
        rating_info = product.get('Rating', {}) or {}
        stockcode = product.get('Stockcode')
        url_slug = product.get('UrlFriendlyName')

        # --- URL ---
        product_url = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{url_slug}" if stockcode and url_slug else None

        # --- Tags ---
        tags = []
        if product.get('IsNew'):
            tags.append('new')
        if attrs.get('lifestyleanddietarystatement'):
            tags.extend([tag.strip() for tag in attrs['lifestyleanddietarystatement'].split(',')])
        if product.get('ImageTag', {}).get('FallbackText'):
            tags.append(product['ImageTag']['FallbackText'])
        
        # --- Categories ---
        try:
            categories = json.loads(attrs.get('piescategorynamesjson', '[]'))
        except (json.JSONDecodeError, TypeError):
            categories = []

        clean_product = {
            "product_id_store": str(stockcode) if stockcode else None,
            "barcode": product.get('Barcode'),
            "name": product.get('Name'),
            "brand": product.get('Brand'),
            "description_short": product.get('Description'),
            "description_long": attrs.get('description'),
            "url": product_url,
            "image_url_main": product.get('LargeImageFile'),
            "image_urls_all": [product.get(f'{size}ImageFile') for size in ['Small', 'Medium', 'Large'] if product.get(f'{size}ImageFile')],

            # --- Pricing ---
            "price_current": product.get('Price'),
            "price_was": product.get('WasPrice'),
            "is_on_special": product.get('IsOnSpecial', False),
            "price_save_amount": product.get('SavingsAmount'),
            "promotion_type": product.get('CentreTag', {}).get('TagType'),
            "price_unit": product.get('CupPrice'),
            "unit_of_measure": product.get('CupMeasure'),
            "unit_price_string": product.get('CupString'),

            # --- Availability & Stock ---
            "is_available": product.get('IsAvailable', False),
            "stock_level": "In Stock" if product.get('IsInStock') else "Out of Stock",
            "purchase_limit": product.get('SupplyLimit'),

            # --- Details & Attributes ---
            "package_size": product.get('PackageSize'),
            "country_of_origin": attrs.get('countryoforigin'),
            "health_star_rating": float(attrs['healthstarrating']) if attrs.get('healthstarrating') else None,
            "ingredients": attrs.get('ingredients'),
            "allergens_may_be_present": [allergen.strip() for allergen in attrs['allergenmaybepresent'].split(',')] if attrs.get('allergenmaybepresent') else [],

            # --- Categorization ---
            "category_main": attrs.get('sapcategoryname'),
            "category_sub": attrs.get('sapsubcategoryname'),
            "tags": list(set(tags)), # Remove duplicates

            # --- Ratings ---
            "rating_average": rating_info.get('Average'),
            "rating_count": rating_info.get('ReviewCount'),
        }
        cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "company": company,
            "store_name": store_name,
            "store_id": store_id,
            "state": state,
            "category": category,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }