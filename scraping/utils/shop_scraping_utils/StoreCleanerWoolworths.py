from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner
from .store_field_maps import WOOLWORTHS_STORE_MAP_API1, WOOLWORTHS_STORE_MAP_API2

class StoreCleanerWoolworths(BaseStoreCleaner):
    """
    Concrete cleaner class for Woolworths store data.
    Handles two different data_management formats.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)
        self.api_format = self._determine_api_format()

    @property
    def field_map(self):
        """Returns the correct field map based on the detected data_management format."""
        if self.api_format == 1:
            return WOOLWORTHS_STORE_MAP_API1
        elif self.api_format == 2:
            return WOOLWORTHS_STORE_MAP_API2
        return {}

    def _determine_api_format(self) -> int:
        """Detects which data_management format the raw data is in."""
        if 'StoreNo' in self.raw_store_data:
            return 1
        if 'FulfilmentStoreId' in self.raw_store_data:
            return 2
        return 0 # Unknown format

    def _transform_store(self) -> dict:
        """
        Transforms a single raw Woolworths store data dictionary into the standardized schema.
        """
        if self.api_format == 0:
            return {} # Return empty dict for unknown formats

        # Use the base class helper to get all fields defined in the map
        cleaned_data = {
            standard_field: self._get_value(standard_field)
            for standard_field in self.field_map.keys()
        }

        # --- Handle special cases and transformations --- 

        cleaned_data['is_active'] = True

        if self.api_format == 1:
            # Handle the 'N/A' store name case for data_management 1
            if cleaned_data.get('store_name') == 'N/A' and cleaned_data.get('suburb'):
                cleaned_data['store_name'] = cleaned_data['suburb']

        # You could add more specific transformations for data_management 2 here if needed
        # For example, parsing state from AddressText, etc.

        return cleaned_data