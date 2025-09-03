from datetime import datetime
from django.utils.text import slugify
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import COLES_FIELD_MAP

class DataCleanerColes(BaseDataCleaner):
    """
    Concrete cleaner class for Coles product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    @property
    def field_map(self):
        return COLES_FIELD_MAP

    def _is_valid_product(self, raw_product: dict) -> bool:
        # Coles search results include non-product tiles we need to filter out.
        return super()._is_valid_product(raw_product) and raw_product.get('_type') == 'PRODUCT'

    def _transform_product(self, raw_product: dict) -> dict:
        """
        Transforms a single raw Coles product into the standardized schema
        using the field map.
        """
        # Use the base class helper to get most fields
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for Coles ---

        # Was price is 0 if not on special, convert to None
        if cleaned_product.get('price_was') == 0:
            cleaned_product['price_was'] = None

        # Combine price info
        price_info = self._calculate_price_info(
            current_price=cleaned_product.get('price_current'),
            was_price=cleaned_product.get('price_was')
        )
        cleaned_product.update(price_info)

        # Category path needs to be extracted from a nested dict
        raw_category_dict = cleaned_product.get('category_path', {}) or {}
        raw_category_path = [
            raw_category_dict.get('aisle'),
            raw_category_dict.get('category'),
            raw_category_dict.get('subCategory')
        ]
        cleaned_product['category_path'] = self._clean_category_path(raw_category_path)

        # Image URL needs the domain prepended
        if cleaned_product.get('image_url'):
            cleaned_product['image_url'] = f"https://www.coles.com.au{cleaned_product['image_url']}"

        # Construct full URL
        product_id = cleaned_product.get('product_id_store')
        product_name = cleaned_product.get('name')
        if product_id and product_name:
            slug = slugify(product_name)
            cleaned_product['url'] = f"https://www.coles.com.au/product/{slug}-{product_id}"

        # Standardize unit price
        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        cleaned_product['is_available'] = raw_product.get('availability', False)

        return cleaned_product