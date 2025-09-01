from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner

class StoreCleanerAldi(BaseStoreCleaner):
    """
    Concrete cleaner class for ALDI store data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    def _transform_store(self) -> dict:
        """
        Transforms a single raw ALDI store data dictionary into the standardized schema.
        """
        store_id = self.raw_store_data.get('id')
        address_data = self.raw_store_data.get('address', {})

        cleaned_data = {
            "store_name": self.raw_store_data.get('name'),
            "store_id": store_id,
            "retailer_store_id": None,
            "is_active": True,
            "division": None,
            "email": None,
            "phone_number": self.raw_store_data.get('publicPhoneNumber'),
            "address_line_1": address_data.get('address1'),
            "address_line_2": address_data.get('address2'),
            "suburb": address_data.get('city'),
            "city": address_data.get('city'),
            "state": address_data.get('regionName'),
            "postcode": address_data.get('zipCode'),
            "latitude": address_data.get('latitude'),
            "longitude": address_data.get('longitude'),
            "trading_hours": None,
            "facilities": self.raw_store_data.get('facilities'),
            "is_trading": self.raw_store_data.get('isOpenNow'),
            "online_shop_url": None,
            "store_url": None,
            "ecommerce_url": None,
            "record_id": None,
            "status": None,
            "store_type": None,
            "site_id": None,
            "shopping_modes": None,
            "available_customer_service_types": self.raw_store_data.get('availableCustomerServiceTypes'),
            "alcohol_availability": self.raw_store_data.get('alcoholAvailability'),
        }
        return cleaned_data
