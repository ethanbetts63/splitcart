from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner

class StoreCleanerIga(BaseStoreCleaner):
    """
    Concrete cleaner class for IGA store data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    def _transform_store(self) -> dict:
        """
        Transforms a single raw IGA store data dictionary into the standardized schema.
        """
        cleaned_data = {
            "store_name": self.raw_store_data.get('storeName'),
            "store_id": self.raw_store_data.get('storeId'),
            "retailer_store_id": self.raw_store_data.get('tag'),
            "is_active": True,  # Assuming all discovered stores are active
            "division": None,  # IGA doesn't seem to have divisions in the same way as Coles/Woolies
            "email": self.raw_store_data.get('email'),
            "phone_number": self.raw_store_data.get('phone'),
            "address_line_1": self.raw_store_data.get('address'),
            "address_line_2": None,
            "suburb": self.raw_store_data.get('suburb'),
            "state": self.raw_store_data.get('state'),
            "postcode": self.raw_store_data.get('postcode'),
            "latitude": self.raw_store_data.get('latitude'),
            "longitude": self.raw_store_data.get('longitude'),
            "trading_hours": self.raw_store_data.get('hours'),
            "facilities": None,
            "is_trading": None, # Not available in IGA data
            "online_shop_url": self.raw_store_data.get('onlineShopUrl'),
            "store_url": self.raw_store_data.get('storeUrl'),
            "ecommerce_url": self.raw_store_data.get('ecommerceUrl'),
            "record_id": self.raw_store_data.get('id'),
            "status": self.raw_store_data.get('status'),
            "store_type": self.raw_store_data.get('type'),
            "site_id": self.raw_store_data.get('siteId'),
            "shopping_modes": self.raw_store_data.get('shoppingModes'),
            "available_customer_service_types": None,
            "alcohol_availability": None,
        }
        return cleaned_data
