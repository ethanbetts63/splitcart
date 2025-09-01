from abc import ABC, abstractmethod
from datetime import datetime
from api.utils.product_normalizer import ProductNormalizer
from api.utils.price_normalizer import PriceNormalizer
from .wrap_cleaned_products import wrap_cleaned_products

class BaseDataCleaner(ABC):
    """
    Abstract base class for cleaning raw product data from a specific store.
    It orchestrates the cleaning process, separating store-specific transformation
    from generic, common normalization.
    """
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime):
        self.raw_product_list = raw_product_list or []
        self.company = company
        self.store_name = store_name
        self.store_id = store_id
        self.state = state
        self.timestamp = timestamp
        self.cleaned_products = []
        self.final_products = []

    @property
    @abstractmethod
    def field_map(self) -> dict:
        """Subclasses must provide their field mapping dictionary."""
        raise NotImplementedError

    def _get_value(self, raw_product: dict, standard_field: str):
        """
        Gets a value from the raw product dict using the field_map.
        Handles dot notation for nested objects.
        """
        raw_field_key = self.field_map.get(standard_field)
        if not raw_field_key:
            return None
        
        # Simple key
        if '.' not in raw_field_key:
            return raw_product.get(raw_field_key)
        
        # Nested key (e.g., 'price.current')
        value = raw_product
        for key_part in raw_field_key.split('.'):
            if not isinstance(value, dict):
                return None
            value = value.get(key_part)
        return value

    def clean_data(self) -> dict:
        """
        Main orchestration method.
        1. Transforms raw data using store-specific logic.
        2. Performs common post-processing and normalization.
        3. Wraps the final data with metadata.
        """
        # 1. Store-specific cleaning
        for raw_product in self.raw_product_list:
            if not self._is_valid_product(raw_product):
                continue
            cleaned_product = self._transform_product(raw_product)
            if cleaned_product:
                self.cleaned_products.append(cleaned_product)

        # 2. Common post-processing
        for p in self.cleaned_products:
            processed_product = self._post_process_product(p)
            self.final_products.append(processed_product)

        # 3. Wrap for output
        return wrap_cleaned_products(
            products=self.final_products,
            company=self.company,
            store_name=self.store_name,
            store_id=self.store_id,
            state=self.state,
            timestamp=self.timestamp
        )

    def _is_valid_product(self, raw_product: dict) -> bool:
        """
        Optional hook for subclasses to perform initial validation on a raw product item.
        """
        return raw_product is not None

    @abstractmethod
    def _transform_product(self, raw_product: dict) -> dict:
        """
        Abstract method to be implemented by subclasses.
        Transforms a single raw product from a specific store into the
        standardized clean product schema.
        """
        raise NotImplementedError

    def _post_process_product(self, product: dict) -> dict:
        """
        Performs generic normalization and key generation on a cleaned product.
        This logic is common across all cleaners.
        """
        # Product Normalization
        normalizer = ProductNormalizer(product)
        product['sizes'] = normalizer.get_raw_sizes()
        product['normalized_name_brand_size'] = normalizer.get_normalized_string()
        if 'barcode' in product and product.get('barcode'):
             product['barcode'] = normalizer.get_cleaned_barcode()

        # Price Normalization & Date
        price_normalizer = PriceNormalizer()
        product['normalized_key'] = price_normalizer.get_normalized_key(
            product_id=product.get('product_id_store'),
            store_id=self.store_id,
            price=product.get('price_current'),
            date=self.timestamp.date().isoformat()
        )
        product['scraped_date'] = self.timestamp.date().isoformat()

        return product

    def _calculate_price_info(self, current_price: float | None, was_price: float | None) -> dict:
        """
        Calculates derived price fields based on current and was prices.
        """
        is_on_special = was_price is not None and current_price is not None and was_price > current_price
        save_amount = round(was_price - current_price, 2) if is_on_special else None
        
        return {
            "price_current": current_price,
            "price_was": was_price,
            "is_on_special": is_on_special,
            "price_save_amount": save_amount,
        }

    def _clean_category_path(self, path_list: list) -> list:
        """
        Cleans a list of category strings by stripping whitespace and applying title case.
        """
        if not path_list:
            return []
        return [str(part).strip().title() for part in path_list if part]
