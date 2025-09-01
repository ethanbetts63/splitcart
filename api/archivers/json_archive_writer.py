
import os
import json
from django.conf import settings

class JsonArchiveWriter:
    """
    A utility class to handle the saving of JSON files.
    """

    def __init__(self, base_archive_dir=None):
        if base_archive_dir:
            self.base_archive_dir = base_archive_dir
        else:
            self.base_archive_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive')

    def save_store_data(self, company_slug, store_id, data_dict):
        """
        Saves store-specific data to a JSON file.
        """
        directory_path = os.path.join(self.base_archive_dir, 'store_data', company_slug)
        os.makedirs(directory_path, exist_ok=True)
        file_path = os.path.join(directory_path, f"{store_id}.json")
        self._write_json(file_path, data_dict)
        return file_path

    def save_company_data(self, company_slug, data_dict):
        """
        Saves company-level data to a JSON file.
        """
        directory_path = os.path.join(self.base_archive_dir, 'company_data')
        os.makedirs(directory_path, exist_ok=True)
        file_path = os.path.join(directory_path, f"{company_slug}.json")
        self._write_json(file_path, data_dict)
        return file_path

    def _write_json(self, file_path, data_dict):
        """
        Writes a dictionary to a JSON file.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=4)
