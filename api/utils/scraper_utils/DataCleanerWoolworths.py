import json
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import WOOLWORTHS_FIELD_MAP
from api.utils.product_normalizer import ProductNormalizer

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
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for Woolworths ---

        price_info = self._calculate_price_info(
            current_price=cleaned_product.get('price_current'),
            was_price=cleaned_product.get('price_was')
        )
        cleaned_product.update(price_info)

        # --- THE FIX: Assemble category path from multiple fragmented fields ---
        def parse_json_field(field_name):
            raw_json_str = self._get_value(raw_product, field_name)
            if not raw_json_str or not isinstance(raw_json_str, str):
                return []
            try:
                return json.loads(raw_json_str)
            except json.JSONDecodeError:
                return []

        # Define the paths to the raw fields
        dept_field = 'AdditionalAttributes.piesdepartmentnamesjson'
        cat_field = 'AdditionalAttributes.piescategorynamesjson'
        subcat_field = 'AdditionalAttributes.piessubcategorynamesjson'

        # Extract and parse each part of the hierarchy
        departments = parse_json_field(dept_field)
        categories = parse_json_field(cat_field)
        subcategories = parse_json_field(subcat_field)

        # Combine them into a single path, preserving order and removing duplicates
        full_path = []
        seen = set()
        for item in departments + categories + subcategories:
            if item and item not in seen:
                seen.add(item)
                full_path.append(item)

        cleaned_product['category_path'] = self._clean_category_path(full_path)

        # --- Other transformations ---
        stockcode = cleaned_product.get('product_id_store')
        slug = cleaned_product.get('url')
        if stockcode and slug:
            cleaned_product['url'] = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{slug}"

        hsr = cleaned_product.get('health_star_rating')
        if hsr:
            try:
                cleaned_product['health_star_rating'] = float(hsr)
            except (ValueError, TypeError):
                cleaned_product['health_star_rating'] = None

        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        cleaned_product['is_available'] = raw_product.get('IsAvailable', False)

        normalizer = ProductNormalizer(cleaned_product)
        cleaned_product['normalized_name'] = normalizer.get_fully_normalized_name()

        return cleaned_product
