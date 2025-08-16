from datetime import datetime
from django.utils.text import slugify

def _create_coles_url_slug(product_name: str, product_size: str) -> str:
    """Helper function to create a URL slug from product name and size."""
    if not product_name or not product_size:
        return ""
    # Remove size from name if it's already there
    name_lower = product_name.lower()
    size_lower = product_size.lower()
    if name_lower.endswith(size_lower):
        name_lower = name_lower[:-len(size_lower)].strip()
    
    return slugify(name_lower)

def clean_raw_data_coles(raw_product_list: list, company: str, store_id: str, store_name: str, state: str, category: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Coles product data according to the V2 schema and
    wraps it in a dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    if not raw_product_list:
        raw_product_list = []

    for product in raw_product_list:
        if not product or product.get('_type') != 'PRODUCT':
            continue

        pricing = product.get('pricing', {}) or {}
        unit_info = pricing.get('unit', {}) or {}
        online_heirs = product.get('onlineHeirs', [{}])[0] or {}
        restrictions = product.get('restrictions', {}) or {}
        image_uris = product.get('imageUris', []) or []

        # --- Basic Info ---
        product_id = product.get('id')
        product_name = product.get('name')
        product_size = product.get('size')
        
        # --- URL ---
        product_url = None
        if product_id and product_name and product_size:
            slug = _create_coles_url_slug(product_name, product_size)
            product_url = f"https://www.coles.com.au/product/{slug}-{product_id}"

        # --- Pricing ---
        price_now = pricing.get('now')
        price_was = pricing.get('was') if pricing.get('was') != 0 else None
        
        # --- Tags & Promotions ---
        tags = []
        if pricing.get('promotionType') == 'SPECIAL':
            tags.append('special')

        # --- Category Hierarchy ---
        category_path = []
        if online_heirs:
            sub_cat = online_heirs.get('subCategory')
            cat = online_heirs.get('category')
            aisle = online_heirs.get('aisle')
            if sub_cat:
                category_path.append(sub_cat.strip().title())
            if cat:
                category_path.append(cat.strip().title())
            if aisle:
                category_path.append(aisle.strip().title())
        
        clean_product = {
            "product_id_store": str(product_id) if product_id else None,
            "barcode": None,  # Not available in Coles data
            "name": product_name,
            "brand": product.get('brand'),
            "description_short": product.get('description'),
            "description_long": None, # Not available in Coles data
            "url": product_url,
            "image_url_main": f"https://www.coles.com.au{image_uris[0]['uri']}" if image_uris else None,
            "image_urls_all": [f"https://www.coles.com.au{img['uri']}" for img in image_uris],

            # --- Pricing ---
            "price_current": price_now,
            "price_was": price_was,
            "is_on_special": pricing.get('onlineSpecial', False),
            "price_save_amount": pricing.get('saveAmount'),
            "promotion_type": pricing.get('promotionType'),
            "price_unit": unit_info.get('price'),
            "unit_of_measure": unit_info.get('ofMeasureUnits'),
            "unit_price_string": pricing.get('comparable'),

            # --- Availability & Stock ---
            "is_available": product.get('availability', False),
            "stock_level": None, # Not available
            "purchase_limit": restrictions.get('retailLimit'),

            # --- Details & Attributes ---
            "package_size": product_size,
            "country_of_origin": None, # Not available
            "health_star_rating": None, # Not available
            "ingredients": None, # Not available in this part of the data

            # --- Categorization ---
            "category_path": category_path,
            "tags": tags,
            
            # --- Ratings ---
            "rating_average": None, # Not available
            "rating_count": None, # Not available
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