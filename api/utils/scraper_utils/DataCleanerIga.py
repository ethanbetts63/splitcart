from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import IGA_FIELD_MAP

class DataCleanerIga(BaseDataCleaner):
    """
    Concrete cleaner class for IGA product data.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp)

    @property
    def field_map(self):
        return IGA_FIELD_MAP

    def _transform_product(self, raw_product: dict) -> dict:
        """
        Transforms a single raw IGA product into the standardized schema
        using the field map.
        """
        # Use the base class helper to get most fields
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for IGA ---

        # IGA has a complex price structure, especially for specials.
        was_price = raw_product.get('wasWholePrice')
        current_price = None
        if was_price:
            # If was_price exists, the current price is in the tprPrice list
            tpr_price_info = raw_product.get('tprPrice', [])
            if tpr_price_info:
                current_price = tpr_price_info[0].get('wholePrice')
        else:
            current_price = raw_product.get('wholePrice')

        # Fallback to priceNumeric if other fields are missing
        if current_price is None:
            current_price = cleaned_product.get('price_current')

        price_info = self._calculate_price_info(current_price, was_price)
        cleaned_product.update(price_info)

        # Category path is a breadcrumb string that needs splitting
        raw_breadcrumb = cleaned_product.get('category_path', '') or ''
        category_parts = [part for part in raw_breadcrumb.split('/') if part]
        cleaned_product['category_path'] = self._clean_category_path(category_parts)

        # Package size needs to be constructed from unitOfSize
        size_value = cleaned_product.get('package_size') # Mapped to unitOfSize.size
        size_type = raw_product.get('unitOfSize', {}).get('abbreviation')
        package_size_str = ""
        if size_value and size_type:
            package_size_str = f"{size_value}{size_type}"
        
        sell_by = raw_product.get('sellBy')
        if sell_by:
            package_size_str += f" {sell_by}"

        cleaned_product['package_size'] = package_size_str.strip()

        # Handle availability
        cleaned_product['is_available'] = raw_product.get('available', False)

        # Standardize unit price
        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        return cleaned_product