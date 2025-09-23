from abc import ABC, abstractmethod
from datetime import datetime

class BaseStoreCleaner(ABC):
    """
    Abstract base class for cleaning raw store data from a specific company.
    It orchestrates the cleaning process, using a field map for simple transformations
    and allowing for complex, store-specific logic.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        self.raw_store_data = raw_store_data
        self.company = company
        self.timestamp = timestamp

    @property
    @abstractmethod
    def field_map(self) -> dict:
        """Subclasses must provide their primary field mapping dictionary."""
        raise NotImplementedError

    def _get_value(self, standard_field: str, field_map: dict = None):
        """
        Gets a value from the raw store dict using the provided field_map.
        If no map is provided, it uses the default one from the property.
        Handles dot notation for nested objects.
        """
        current_map = field_map if field_map is not None else self.field_map
        raw_field_key = current_map.get(standard_field)
        
        if not raw_field_key:
            return None
        
        if '.' not in raw_field_key:
            return self.raw_store_data.get(raw_field_key)
        
        value = self.raw_store_data
        for key_part in raw_field_key.split('.'):
            if not isinstance(value, dict):
                return None
            value = value.get(key_part)
        return value

    def clean(self) -> dict:
        """
        Main orchestration method.
        1. Transforms raw data using store-specific logic.
        2. Wraps the cleaned data with metadata.
        """
        cleaned_data = self._transform_store()
        
        metadata = {
            "company": self.company,
            "scraped_date": self.timestamp.date().isoformat()
        }

        return {
            "metadata": metadata,
            "store_data": cleaned_data
        }

    @abstractmethod
    def _transform_store(self) -> dict:
        """
        Abstract method to be implemented by subclasses.
        Transforms a single raw store data dictionary into the standardized schema.
        """
        raise NotImplementedError