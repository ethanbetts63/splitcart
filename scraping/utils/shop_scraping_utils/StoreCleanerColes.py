from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner
from .store_field_maps import COLES_STORE_MAP

class StoreCleanerColes(BaseStoreCleaner):
    """
    Concrete cleaner class for Coles store data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    @property
    def field_map(self):
        return COLES_STORE_MAP

    def _transform_store(self) -> dict:
        """
        Transforms a single raw Coles store data dictionary into the standardized schema.
        """
        cleaned_data = {
            standard_field: self._get_value(standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations for Coles ---

        # Clean postcode
        raw_postcode = cleaned_data.get('postcode')
        if raw_postcode:
            cleaned_data['postcode'] = self._clean_postcode(str(raw_postcode))

        cleaned_data['is_active'] = True

        # Determine division from store ID prefix
        store_id = cleaned_data.get('store_id')
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
        cleaned_data['division'] = division

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

    