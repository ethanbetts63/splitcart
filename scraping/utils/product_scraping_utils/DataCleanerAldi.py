import re
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import ALDI_FIELD_MAP
from data_management.utils.product_normalizer import ProductNormalizer

class DataCleanerAldi(BaseDataCleaner):
    """
    Concrete cleaner class for ALDI product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    @property
    def field_map(self):
        return ALDI_FIELD_MAP

    def _transform_product(self, raw_product: dict) -> dict:
        """
        Transforms a single raw ALDI product into the standardized schema
        using the field map.
        """
        # Use the base class helper to get most fields
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for ALDI ---

        # Price is in cents, needs conversion
        if cleaned_product.get('price_current') is not None:
            cleaned_product['price_current'] /= 100.0
        
        if cleaned_product.get('per_unit_price_value') is not None:
            cleaned_product['per_unit_price_value'] /= 100.0

        # Was price needs to be parsed from a string like "$x.xx"
        was_price_str = cleaned_product.get('price_was')
        was_price = None
        if was_price_str and isinstance(was_price_str, str):
            try:
                was_price = float(re.sub(r'[^\d.]', '', was_price_str))
            except (ValueError, TypeError):
                was_price = None
        cleaned_product['price_was'] = was_price

        # Combine price info
        price_info = self._calculate_price_info(
            current_price=cleaned_product.get('price_current'),
            was_price=cleaned_product.get('price_was')
        )
        cleaned_product.update(price_info)

        # Category path needs to be extracted from a list of dicts
        raw_categories = cleaned_product.get('category_path', []) or []
        category_names = [cat.get('name') for cat in raw_categories]
        cleaned_product['category_path'] = self._clean_category_path(category_names)

        # Construct full URL
        slug = cleaned_product.get('url', '')
        sku = cleaned_product.get('sku', '')
        if slug and sku:
            cleaned_product['url'] = f"https://www.aldi.com.au/product/{slug}-{sku}"

        # Construct full IMAGE URL from assets[0].url
        raw_image_url = cleaned_product.get('image_url', '') # This should now be the full URL from assets[0].url
        if raw_image_url:
            # Replace {width} with 500
            processed_url = raw_image_url.replace('{width}', '500')
            
            # Chop off the /{slug} part if it exists
            if processed_url.endswith('/{slug}'):
                processed_url = processed_url[:-len('/{slug}')]
            
            # Assign to image_url_pairs
            cleaned_product['image_url_pairs'] = [[self.company, processed_url]]
        else:
            cleaned_product['image_url_pairs'] = [] # Initialize as empty list if no image URL

        # Remove the old image_url key if it exists, as it's no longer needed
        if 'image_url' in cleaned_product:
            del cleaned_product['image_url']

        # Standardize unit price

        # Standardize unit price
        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        # Handle availability
        cleaned_product['is_available'] = not raw_product.get('notForSale', False)

        # Add normalized name for better matching
        normalizer = ProductNormalizer(cleaned_product)
        cleaned_product['normalized_name'] = normalizer.get_fully_normalized_name()

        return cleaned_product