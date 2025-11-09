from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from data_management.utils.product_normalizer import ProductNormalizer
from data_management.utils.price_normalizer import PriceNormalizer
from data_management.utils.price_hasher import generate_price_hash
from .wrap_cleaned_products import wrap_cleaned_products
from products.models import ProductBrand

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
        self.brand_cache = self._build_brand_cache()

    def _build_brand_cache(self):
        """
        Builds a cache of brand data for the normalizer to use,
        keyed by the normalized brand name.
        """
        brand_cache = {}
        for brand in ProductBrand.objects.all():
            # Use the normalized_name as the key
            brand_cache[brand.normalized_name] = {
                'name': brand.name,  # Include the human-readable name
                'name_variations': brand.name_variations
            }
        return brand_cache

    @property
    @abstractmethod
    def field_map(self) -> dict:
        """Subclasses must provide their field mapping dictionary."""
        raise NotImplementedError

    def _get_value(self, raw_product: dict, standard_field: str):
        """
        Gets a value from the raw product dict using the field_map.
        Handles dot notation for nested objects and lists.
        """
        raw_field_key = self.field_map.get(standard_field)
        if not raw_field_key:
            return None
        
        if '.' not in raw_field_key:
            return raw_product.get(raw_field_key)
        
        value = raw_product
        for key_part in raw_field_key.split('.'):
            if isinstance(value, list):
                try:
                    key_part = int(key_part)
                    value = value[key_part]
                except (ValueError, IndexError):
                    return None
            elif isinstance(value, dict):
                value = value.get(key_part)
            else:
                return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def clean_data(self) -> dict:
        """
        Main orchestration method.
        """
        for raw_product in self.raw_product_list:
            if not self._is_valid_product(raw_product):
                continue
            cleaned_product = self._transform_product(raw_product)
            if cleaned_product:
                self.cleaned_products.append(cleaned_product)

        for p in self.cleaned_products:
            processed_product = self._post_process_product(p)
            self.final_products.append(processed_product)

        return wrap_cleaned_products(
            products=self.final_products,
            company=self.company,
            store_name=self.store_name,
            store_id=self.store_id,
            state=self.state,
            timestamp=self.timestamp
        )

    def _is_valid_product(self, raw_product: dict) -> bool:
        return raw_product is not None

    @abstractmethod
    def _transform_product(self, raw_product: dict) -> dict:
        raise NotImplementedError

    def _post_process_product(self, product: dict) -> dict:
        """
        Performs generic normalization on a cleaned product.
        """
        normalizer = ProductNormalizer(product, self.brand_cache)
        # Overwrite the brand with the canonical version
        product['brand'] = normalizer.cleaned_brand
        # Add the new normalized brand key
        product['normalized_brand'] = normalizer.get_normalized_brand_name()
        product['sizes'] = normalizer.get_raw_sizes()
        product['normalized_name_brand_size'] = normalizer.get_normalized_name_brand_size_string()
        if product.get('barcode') is not None:
             product['barcode'] = normalizer.get_cleaned_barcode()

        product['scraped_date'] = self.timestamp.date().isoformat()

        # Convert all empty string fields to None to ensure consistency
        for key, value in product.items():
            if isinstance(value, str) and not value.strip():
                product[key] = None

        # Generate the price hash after all other fields are set
        product['price_hash'] = generate_price_hash(product, self.store_id)
        
        # Remove keys with None values to optimize file size
        product = {k: v for k, v in product.items() if v is not None}
        
        return product

    def _calculate_price_info(self, current_price: float | None, was_price: float | None) -> dict:
        is_on_special = was_price is not None and current_price is not None and was_price > current_price
        save_amount = round(was_price - current_price, 2) if is_on_special else None
        return {
            "price_current": current_price,
            "price_was": was_price,
            "is_on_special": is_on_special,
            "price_save_amount": save_amount,
        }

    def _get_standardized_unit_price_info(self, price_data: dict) -> dict:
        """
        Uses the PriceNormalizer to extract and calculate a standardized
        unit price (e.g., price per 1kg or 1L).
        """
        normalizer = PriceNormalizer(price_data, self.company)
        
        unit_price = normalizer.get_normalized_unit_price()
        measure_info = normalizer.get_normalized_unit_measure()

        if not all([unit_price, measure_info]):
            return {"unit_price": None, "unit_of_measure": None}

        unit, quantity = measure_info
        final_price = unit_price
        final_measure = f"{quantity}{unit}"

        # Standardize to per 1kg or 1L
        if unit == 'g' and quantity != 1000:
            final_price = (unit_price / quantity) * 1000
            final_measure = "1kg"
        elif unit == 'ml' and quantity != 1000:
            final_price = (unit_price / quantity) * 1000
            final_measure = "1l"
        elif unit == 'kg' and quantity != 1:
            final_price = unit_price / quantity
            final_measure = "1kg"
        elif unit == 'l' and quantity != 1:
            final_price = unit_price / quantity
            final_measure = "1l"

        return {
            "unit_price": round(final_price, 2),
            "unit_of_measure": final_measure
        }

    def _clean_category_path(self, path_list: list) -> list:
        if not path_list:
            return []
        return [str(part).strip().title() for part in path_list if part]