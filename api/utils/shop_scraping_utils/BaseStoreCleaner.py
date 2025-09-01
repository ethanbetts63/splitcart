from abc import ABC, abstractmethod
from datetime import datetime

class BaseStoreCleaner(ABC):
    """
    Abstract base class for cleaning raw store data from a specific company.
    It orchestrates the cleaning process, separating store-specific transformation
    from the final wrapping of the data.
    """
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        self.raw_store_data = raw_store_data
        self.company = company
        self.timestamp = timestamp

    def clean(self) -> dict:
        """
        Main orchestration method.
        1. Transforms raw data using store-specific logic.
        2. Wraps the cleaned data with metadata.
        """
        cleaned_data = self._transform_store()
        
        metadata = {
            "company": self.company,
            "scraped_at": self.timestamp.isoformat()
        }

        # Allow subclasses to add extra metadata if needed
        extra_metadata = self._get_extra_metadata()
        metadata.update(extra_metadata)

        return {
            "metadata": metadata,
            "store_data": cleaned_data
        }

    def _get_extra_metadata(self) -> dict:
        """
        Optional hook for subclasses to add company-specific metadata.
        """
        return {}

    @abstractmethod
    def _transform_store(self) -> dict:
        """
        Abstract method to be implemented by subclasses.
        Transforms a single raw store data dictionary into the standardized schema.
        """
        raise NotImplementedError
