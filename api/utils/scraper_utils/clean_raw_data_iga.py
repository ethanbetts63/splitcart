from datetime import datetime
import re
from api.utils.product_normalizer import ProductNormalizer
from api.utils.scraper_utils.wrap_cleaned_products import wrap_cleaned_products

def clean_raw_data_iga(raw_product_list: list, company: str, store_id: str, store_name: str, state: str, timestamp: datetime) -> dict:
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

        is_on_special = 'wasWholePrice' in product
        current_price = None
        was_price = None
        save_amount = None

        if is_on_special:
            was_price = product.get('wasWholePrice')
            tpr_price_info = product.get('tprPrice', [])
            if tpr_price_info:
                current_price = tpr_price_info[0].get('wholePrice')
        else:
            current_price = product.get('wholePrice')

        if current_price is None:
            current_price = product.get('priceNumeric')
        
        if was_price and current_price:
            save_amount = round(was_price - current_price, 2)

        category_path = []
        category_hierarchy = product.get('categories', [])
        if category_hierarchy:
            last_category = category_hierarchy[-1]
            breadcrumb = last_category.get('categoryBreadcrumb', '')
            if breadcrumb:
                category_path = [part.strip().title() for part in breadcrumb.split('/') if part]

        description = product.get('description', '')
        country_of_origin = None

        image_info = product.get('image', {}) or {}
        image_urls = [url for url in image_info.values() if url]

        price_unit = None
        unit_of_measure = None
        price_per_unit_string = product.get('pricePerUnit')
        if price_per_unit_string:
            match = re.search(r'\$([\d.]+)/(.+)', price_per_unit_string)
            if match:
                try:
                    price_unit = float(match.group(1))
                    unit_of_measure = match.group(2).strip().lower()
                except ValueError:
                    pass

        unit_of_size_info = product.get('unitOfSize')
        sell_by_info = product.get('sellBy')
        package_size_str = None
        
        size_parts = []
        if unit_of_size_info:
            size = unit_of_size_info.get('size')
            size_type = unit_of_size_info.get('type')
            if size and size_type:
                size_parts.append(f"{size}{size_type}")
        
        if sell_by_info:
            size_parts.append(sell_by_info)
            
        if size_parts:
            package_size_str = " ".join(size_parts)

        clean_product = {
            "product_id_store": product.get('sku'),
            "barcode": product.get('barcode'), # Pass raw barcode to be cleaned by normalizer
            "name": product.get('name') if product.get('name') else None,
            "brand": product.get('brand') if product.get('brand') else None,
            "description_short": None,
            "description_long": description.strip() if description else None,
            "url": None,
            "image_url_main": image_info.get('default'),
            "image_urls_all": image_urls,
            "price_current": current_price,
            "price_was": was_price,
            "is_on_special": is_on_special,
            "price_save_amount": save_amount,
            "promotion_type": product.get('priceSource'),
            "price_unit": price_unit,
            "unit_of_measure": unit_of_measure,
            "unit_price_string": product.get('pricePerUnit'),
            "is_available": product.get('available'),
            "stock_level": None,
            "purchase_limit": None,
            "package_size": package_size_str,
            "country_of_origin": country_of_origin,
            "health_star_rating": None,
            "ingredients": None,
            "allergens_may_be_present": None,
            "category_path": category_path,
            "tags": [],
            "rating_average": None,
            "rating_count": None,
        }
        cleaned_products.append(clean_product)

    # --- Final generic cleaning and normalization ---
    final_products = []
    for p in cleaned_products:
        normalizer = ProductNormalizer(p)
        p['sizes'] = normalizer.get_raw_sizes()
        p['normalized_name_brand_size'] = normalizer.get_normalized_string()
        p['barcode'] = normalizer.get_cleaned_barcode()
        final_products.append(p)
    
    return wrap_cleaned_products(
        products=final_products,
        company=company,
        store_name=store_name,
        store_id=store_id,
        state=state,
        timestamp=timestamp
    )