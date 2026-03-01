import json
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import WOOLWORTHS_FIELD_MAP


def _deep_get(data, keys):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data


def _parse_json_field(raw_product, field_path):
    raw_json_str = _deep_get(raw_product, field_path.split('.'))
    if not raw_json_str or not isinstance(raw_json_str, str):
        return []
    try:
        return json.loads(raw_json_str)
    except json.JSONDecodeError:
        return []

class DataCleanerWoolworths(BaseDataCleaner):
    """
    Concrete cleaner class for Woolworths product data.
    """
    INVALID_CATEGORIES = {"Footy Finals Kiosk"}

    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime, brand_translations: dict = None, product_translations: dict = None):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp, brand_translations, product_translations)

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

        departments = _parse_json_field(raw_product, 'AdditionalAttributes.piesdepartmentnamesjson')
        categories = _parse_json_field(raw_product, 'AdditionalAttributes.piescategorynamesjson')
        subcategories = _parse_json_field(raw_product, 'AdditionalAttributes.piessubcategorynamesjson')

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

        hsr = cleaned_product.get('health_star_rating')
        if hsr:
            try:
                cleaned_product['health_star_rating'] = float(hsr)
            except (ValueError, TypeError):
                cleaned_product['health_star_rating'] = None

        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        cleaned_product['is_available'] = raw_product.get('IsAvailable', False)

        return cleaned_product
