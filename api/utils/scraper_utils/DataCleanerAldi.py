import re
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner

class DataCleanerAldi(BaseDataCleaner):
    """
    Concrete cleaner class for ALDI product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    def _transform_product(self, product: dict) -> dict:
        """
        Transforms a single raw ALDI product into the standardized schema.
        """
        price_info = product.get('price', {}) or {}

        # --- Price Transformation ---
        current_price = price_info.get('amount')
        if current_price is not None:
            current_price /= 100.0

        comparison_price = price_info.get('comparison')
        if comparison_price is not None:
            comparison_price /= 100.0

        was_price_str = price_info.get('wasPriceDisplay')
        was_price = None
        if was_price_str:
            try:
                was_price = float(re.sub(r'[^\d.]', '', was_price_str))
            except (ValueError, TypeError):
                was_price = None
        
        price_info = self._calculate_price_info(current_price, was_price)

        # --- Unit of Measure ---
        unit_of_measure = None
        comparison_display = price_info.get('comparisonDisplay')
        if comparison_display:
            match = re.search(r'/\s*(.*)', comparison_display)
            if match:
                unit_of_measure = match.group(1).strip()

        # --- Category Hierarchy ---
        raw_category_names = [cat.get('name') for cat in product.get('categories', [])]
        category_path = self._clean_category_path(raw_category_names)

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
            **price_info,
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
        return clean_product
