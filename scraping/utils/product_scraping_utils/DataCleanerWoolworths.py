from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import WOOLWORTHS_FIELD_MAP


class DataCleanerWoolworths(BaseDataCleaner):
    """
    Concrete cleaner class for Woolworths product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime, brand_translations: dict = None, product_translations: dict = None):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp, brand_translations, product_translations)

    @property
    def field_map(self):
        return WOOLWORTHS_FIELD_MAP

    def _clean_context_category_path(self, category_path):
        cleaned_path = self._clean_category_path(category_path)
        deduped_path = []
        seen = set()
        for item in cleaned_path:
            if item not in seen:
                seen.add(item)
                deduped_path.append(item)
        return deduped_path

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

        cleaned_product['category_path'] = self._clean_context_category_path(raw_product.get('category_path', []))

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
