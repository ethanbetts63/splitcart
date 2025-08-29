from datetime import datetime
import re
from api.utils.normalizer import ProductNormalizer
from .wrap_cleaned_products import wrap_cleaned_products


def clean_raw_data_aldi(raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime) -> dict:
    """
    Cleans a list of raw ALDI product data according to the V2 schema and
    wraps it in a dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    if not raw_product_list:
        raw_product_list = []

    for product in raw_product_list:
        if not product:
            continue

        price_info = product.get('price', {}) or {}
        
        # --- Price Transformation ---
        current_price = price_info.get('amount')
        if current_price is not None:
            current_price /= 100.0

        comparison_price = price_info.get('comparison')
        if comparison_price is not None:
            comparison_price /= 100.0

        was_price = price_info.get('wasPriceDisplay') # This seems to be a string, not a number
        if was_price:
            try:
                # Attempt to extract a float from a string like '$5.99'
                was_price = float(re.sub(r'[^\d.]', '', was_price))
            except (ValueError, TypeError):
                was_price = None

        # --- Unit of Measure ---
        unit_of_measure = None
        comparison_display = price_info.get('comparisonDisplay')
        if comparison_display:
            match = re.search(r'/\s*(.*)', comparison_display)
            if match:
                unit_of_measure = match.group(1).strip()

        # --- Category Hierarchy ---
        category_path = []
        category_hierarchy = product.get('categories', [])
        for category in category_hierarchy:
            name = category.get('name')
            if name:
                category_path.append(name.strip().title())

        # --- Image URLs ---
        assets = product.get('assets', []) or []
        image_urls = [asset.get('url') for asset in assets if asset.get('url')]
        main_image = image_urls[0] if image_urls else None

        # --- Tags ---
        tags = [badge.get('badgeText') for badge in product.get('badges', []) if badge.get('badgeText')]

        sku = product.get('sku')
        slug = product.get('urlSlugText', '')
        product_url = f"https://www.aldi.com.au/product/{slug}-{sku}" if slug and sku else None

        clean_product = {
            "product_id_store": sku,
            "barcode": None, # Not available
            "name": product.get('name'),
            "brand": product.get('brandName', ''),
            "description_short": None, # Not available
            "description_long": None, # Not available
            "url": product_url,
            "image_url_main": main_image,
            "image_urls_all": image_urls,

            # --- Pricing ---
            "price_current": current_price,
            "price_was": was_price,
            "is_on_special": was_price is not None,
            "price_save_amount": round(was_price - current_price, 2) if was_price and current_price else None,
            "promotion_type": None, # Not available
            "price_unit": comparison_price,
            "unit_of_measure": unit_of_measure,
            "unit_price_string": comparison_display,

            # --- Availability & Stock ---
            "is_available": not product.get('notForSale', True),
            "stock_level": None, # Not available
            "purchase_limit": product.get('quantityMax'),

            # --- Details & Attributes ---
            "package_size": product.get('sellingSize').lower().strip() if product.get('sellingSize') else None,
            "country_of_origin": None, # Not available
            "health_star_rating": None, # Not available
            "ingredients": None, # Not available
            "allergens_may_be_present": None, # Not available

            # --- Categorization ---
            "category_path": category_path,
            "tags": tags,

            # --- Ratings ---
            "rating_average": None, # Not available
            "rating_count": None, # Not available
        }
        cleaned_products.append(clean_product)

    # --- Final generic cleaning and normalization ---
    final_products = []
    for p in cleaned_products:
        normalizer = ProductNormalizer(p)
        p['sizes'] = normalizer.get_raw_sizes()
        p['normalized_name_brand_size'] = normalizer.get_normalized_string()
        final_products.append(p)
    
    return wrap_cleaned_products(
        products=final_products,
        company=company,
        store_name=store_name,
        store_id=store_id,
        state=state,
        timestamp=timestamp
    )
