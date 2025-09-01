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
