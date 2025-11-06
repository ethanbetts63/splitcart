import json
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import WOOLWORTHS_FIELD_MAP
from data_management.utils.product_normalizer import ProductNormalizer

class DataCleanerWoolworths(BaseDataCleaner):
    """
    Concrete cleaner class for Woolworths product data.
    """
    INVALID_CATEGORIES = {"Footy Finals Kiosk"}

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

        price_info = self._calculate_price_info(
            current_price=cleaned_product.get('price_current'),
            was_price=cleaned_product.get('price_was')
        )
        cleaned_product.update(price_info)

        def deep_get(data, keys):
            for key in keys:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    return None
            return data

        def parse_json_field(field_path):
            raw_json_str = deep_get(raw_product, field_path.split('.'))
            if not raw_json_str or not isinstance(raw_json_str, str):
                return []
            try:
                return json.loads(raw_json_str)
            except json.JSONDecodeError:
                return []

        dept_field = 'AdditionalAttributes.piesdepartmentnamesjson'
        cat_field = 'AdditionalAttributes.piescategorynamesjson'
        subcat_field = 'AdditionalAttributes.piessubcategorynamesjson'

        departments = parse_json_field(dept_field)
        categories = parse_json_field(cat_field)
        subcategories = parse_json_field(subcat_field)

        full_path = []
        seen = set()
        for item in departments + categories + subcategories:
            if item and item not in seen:
                seen.add(item)
                full_path.append(item)
        
        # THE NEW CHANGE: Filter out invalid categories
        final_path = [item for item in full_path if item not in self.INVALID_CATEGORIES]

        cleaned_product['category_path'] = self._clean_category_path(final_path)

        stockcode = cleaned_product.get('sku')
        slug = cleaned_product.get('url')
        if stockcode and slug:
            cleaned_product['url'] = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{slug}"

        # Construct image_url_pairs
        image_url = cleaned_product.get('image_url')
        if image_url:
            cleaned_product['image_url_pairs'] = [[self.company, image_url]]
        else:
            cleaned_product['image_url_pairs'] = []
        
        # Remove the old image_url key
        if 'image_url' in cleaned_product:
            del cleaned_product['image_url']

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