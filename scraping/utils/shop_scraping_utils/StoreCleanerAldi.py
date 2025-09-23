from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner
from .store_field_maps import ALDI_STORE_MAP

class StoreCleanerAldi(BaseStoreCleaner):
    """
    Concrete cleaner class for ALDI store data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    @property
    def field_map(self):
        return ALDI_STORE_MAP

    def _transform_store(self) -> dict:
        """
        Transforms a single raw ALDI store data dictionary into the standardized schema.
        """
        cleaned_data = {
            standard_field: self._get_value(standard_field)
            for standard_field in self.field_map.keys()
        }

        # Set default values for fields not in the map
        cleaned_data['is_active'] = True
        
        return cleaned_data