import json
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import WOOLWORTHS_FIELD_MAP

class DataCleanerWoolworths(BaseDataCleaner):
    """
    Concrete cleaner class for Woolworths product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    @property
    def field_map(self):
        return WOOLWORTHS_FIELD_MAP

    def _transform_product(self, raw_product: dict) -> dict:
        """
        Transforms a single raw Woolworths product into the standardized schema
        using the field map.
        """
        # Use the base class helper to get most fields
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for Woolworths ---

        # Combine price info
        price_info = self._calculate_price_info(
            current_price=cleaned_product.get('price_current'),
            was_price=cleaned_product.get('price_was')
        )
        cleaned_product.update(price_info)

        # Category path is a JSON string that needs to be parsed
        raw_cat_json = cleaned_product.get('category_path', '[]') or '[]'
        try:
            category_list = json.loads(raw_cat_json)
        except json.JSONDecodeError:
            category_list = []
        cleaned_product['category_path'] = self._clean_category_path(category_list)

        # Construct full URL
        stockcode = cleaned_product.get('product_id_store')
        slug = cleaned_product.get('url')
        if stockcode and slug:
            cleaned_product['url'] = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{slug}"

        # Convert health star rating to float
        hsr = cleaned_product.get('health_star_rating')
        if hsr:
            try:
                cleaned_product['health_star_rating'] = float(hsr)
            except (ValueError, TypeError):
                cleaned_product['health_star_rating'] = None

        # Standardize unit price
        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        return cleaned_product