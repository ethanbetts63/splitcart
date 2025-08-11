from datetime import datetime
import re

def clean_raw_data_iga(raw_product_list: list, company: str, store_id: str, store_name: str, state: str, category_slug: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw IGA product data according to the V2 schema and
    wraps it in a dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    if not raw_product_list:
        raw_product_list = []

    for product in raw_product_list:
        if not product:
            continue

        # --- Price and Special Transformation ---
        is_on_special = bool(product.get('tprPrice'))
        was_price = None
        current_price = None
        save_amount = None
        if is_on_special:
            was_price = product.get('priceNumeric')
            current_price = product.get('tprPrice', [{}])[0].get('price')
            if was_price and current_price:
                save_amount = round(was_price - current_price, 2)
        else:
            current_price = product.get('priceNumeric')

        # --- Category Hierarchy ---
        category_path = []
        category_hierarchy = product.get('categories', [])
        if category_hierarchy:
            # The last category in the list has the full breadcrumb
            last_category = category_hierarchy[-1]
            breadcrumb = last_category.get('categoryBreadcrumb', '')
            if breadcrumb:
                category_path = [part.strip().title() for part in breadcrumb.split('/') if part]

        # --- Description and Attributes ---
        description = product.get('description', '')
        country_of_origin = None
        match = re.search(r"Country of Origin: (.*?)", description, re.IGNORECASE)
        if match:
            country_of_origin = match.group(1).strip()

        # --- Image URLs ---
        image_info = product.get('image', {}) or {}
        image_urls = [url for url in image_info.values() if url] # Filter out nulls

        clean_product = {
            "product_id_store": product.get('sku'),
            "barcode": product.get('barcode'),
            "name": product.get('name'),
            "brand": product.get('brand'),
            "description_short": None, # IGA provides one description field
            "description_long": description,
            "url": None, # No direct URL available
            "image_url_main": image_info.get('default'),
            "image_urls_all": image_urls,

            # --- Pricing ---
            "price_current": current_price,
            "price_was": was_price,
            "is_on_special": is_on_special,
            "price_save_amount": save_amount,
            "promotion_type": product.get('priceSource'), # e.g., 'regular' or 'special'
            "price_unit": None, # Not directly available
            "unit_of_measure": product.get('unitOfMeasure', {}).get('label'),
            "unit_price_string": product.get('pricePerUnit'),

            # --- Availability & Stock ---
            "is_available": product.get('available', False),
            "stock_level": None, # Not available
            "purchase_limit": None, # Not available

            # --- Details & Attributes ---
            "package_size": product.get('sellBy'),
            "country_of_origin": country_of_origin,
            "health_star_rating": None, # Not available
            "ingredients": None, # Not available
            "allergens_may_be_present": None, # Not available

            # --- Categorization ---
            "category_path": category_path,
            "tags": [], # No specific tags available

            # --- Ratings ---
            "rating_average": None, # Not available
            "rating_count": None, # Not available
        }
        cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "company": company.lower(),
            "store_name": store_name,
            "store_id": store_id,
            "state": state,
            "category": category_slug,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }