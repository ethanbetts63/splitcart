from datetime import datetime
from django.utils.text import slugify
from .BaseDataCleaner import BaseDataCleaner

class DataCleanerColes(BaseDataCleaner):
    """
    Concrete cleaner class for Coles product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    def _is_valid_product(self, raw_product: dict) -> bool:
        return super()._is_valid_product(raw_product) and raw_product.get('_type') == 'PRODUCT'

    def _transform_product(self, product: dict) -> dict:
        """
        Transforms a single raw Coles product into the standardized schema.
        """
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
        if product_id and product_name:
            slug = slugify(product_name)
            product_url = f"https://www.coles.com.au/product/{slug}-{product_id}"
        else:
            print(f"DEBUG: URL generation failed for product with ID={product_id} and Name={product_name}")

        # --- Pricing ---
        price_now = pricing.get('now')
        price_was = pricing.get('was') if pricing.get('was') != 0 else None
        price_info = self._calculate_price_info(price_now, price_was)

        # --- Tags & Promotions ---
        tags = []
        if pricing.get('promotionType') == 'SPECIAL':
            tags.append('special')

        # --- Category Hierarchy ---
        raw_category_path = [
            online_heirs.get('aisle'),
            online_heirs.get('category'),
            online_heirs.get('subCategory')
        ]
        category_path = self._clean_category_path(raw_category_path)
        
        clean_product = {
            "product_id_store": str(product_id) if product_id else None,
            "barcode": None,  # Not available in Coles data from list pages. 
            "name": product_name if product_name else None,
            "brand": product.get('brand') if product.get('brand') else None,
            "description_short": product.get('description').strip() if product.get('description') else None,
            "description_long": None, # Not available in Coles data
            "url": product_url,
            "image_url_main": f"https://www.coles.com.au{image_uris[0]['uri']}" if image_uris else None,
            "image_urls_all": [f"https://www.coles.com.au{img['uri']}" for img in image_uris],

            # --- Pricing ---
            **price_info,
            "promotion_type": pricing.get('promotionType'),
            "price_unit": unit_info.get('price'),
            "unit_of_measure": unit_info.get('ofMeasureUnits').lower().strip() if unit_info.get('ofMeasureUnits') else None,
            "unit_price_string": pricing.get('comparable'),

            # --- Availability & Stock ---
            "is_available": product.get('availability', False),
            "stock_level": None, # Not available
            "purchase_limit": restrictions.get('retailLimit'),

            # --- Details & Attributes ---
            "package_size": product_size.strip() if product_size else None,
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
        return clean_product
