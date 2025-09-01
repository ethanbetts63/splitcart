from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner

class StoreCleanerColes(BaseStoreCleaner):
    """
    Concrete cleaner class for Coles store data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    def _transform_store(self) -> dict:
        """
        Transforms a single raw Coles store data dictionary into the standardized schema.
        """
        store_id = self.raw_store_data.get('id')
        address = self.raw_store_data.get('address', {})
        position = self.raw_store_data.get('position', {})

        division_mapping = {
            "COL": "Coles Supermarkets",
            "VIN": "Vintage Cellars",
            "LQR": "Liquorland"
        }
        division = None
        if store_id:
            for prefix, division_name in division_mapping.items():
                if f"{prefix}:" in store_id:
                    division = division_name
                    break

        cleaned_data = {
            "store_name": self.raw_store_data.get('name'),
            "store_id": store_id,
            "retailer_store_id": None,
            "is_active": True,  # Assuming all discovered stores are active
            "division": division,
            "email": None,
            "phone_number": self.raw_store_data.get('phone'),
            "address_line_1": address.get('addressLine'),
            "address_line_2": None,
            "suburb": address.get('suburb'),
            "state": address.get('state'),
            "postcode": address.get('postcode'),
            "latitude": position.get('latitude'),
            "longitude": position.get('longitude'),
            "trading_hours": None,
            "facilities": None,
            "is_trading": self.raw_store_data.get('isTrading'),
            "online_shop_url": None,
            "store_url": None,
            "ecommerce_url": None,
            "record_id": None,
            "status": None,
            "store_type": None,
            "site_id": None,
            "shopping_modes": None,
            "available_customer_service_types": None,
            "alcohol_availability": None,
        }

        # Post-cleaning name adjustment
        suburb = cleaned_data.get('suburb')
        store_name = cleaned_data.get('store_name')
        if store_id and suburb and (not store_name or store_name == 'N/A'):
            if 'COL:' in store_id:
                cleaned_data['store_name'] = f"Coles {suburb}"
            elif 'VIN:' in store_id:
                cleaned_data['store_name'] = f"Vintage Cellars {suburb}"
            elif 'LQR:' in store_id:
                cleaned_data['store_name'] = f"Liquorland {suburb}"
        
        return cleaned_data

    def _get_extra_metadata(self) -> dict:
        """
        Adds the brand to the metadata for Coles stores.
        """
        brand = self.raw_store_data.get('brand', {})
        return {"brand": brand.get('id')}
