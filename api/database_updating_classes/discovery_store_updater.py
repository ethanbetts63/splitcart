import json
from companies.models import Company, Store

class DiscoveryStoreUpdater:
    """
    Processes a single discovered store JSON file and updates the database.
    """

    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        """
        The main public method that orchestrates the update process for a single discovered store.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None, 0

        company_name = data.get('company')
        if not company_name:
            return None, 0

        company_obj = self._get_or_create_company(company_name)
        self._get_or_create_store(company_obj, data)
        
        return company_name, 1

    def _get_or_create_company(self, company_name):
        """
        Gets or creates a company.
        """
        company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
        return company_obj

    def _get_or_create_store(self, company_obj, store_data):
        """
        Gets or creates a store from a flat dictionary of store data.
        """
        store_id = store_data.get('store_id')
        if not store_id:
            return

        # Map flat file fields to store model fields
        store_defaults = {
            'store_name': store_data.get('name'),
            'address_line_1': store_data.get('address'),
            'suburb': store_data.get('suburb'),
            'state': store_data.get('state'),
            'postcode': store_data.get('postcode'),
            'latitude': store_data.get('latitude'),
            'longitude': store_data.get('longitude'),
            'phone_number': store_data.get('phone_number'),
            'is_active': store_data.get('is_active', True),
            'retailer_store_id': store_data.get('retailer_store_id')
        }

        # Remove None values so we don't overwrite existing data with nulls during an update
        update_data = {k: v for k, v in store_defaults.items() if v is not None}

        store, created = Store.objects.get_or_create(
            store_id=store_id,
            company=company_obj,
            defaults=update_data
        )

        if not created:
            # Update existing store
            Store.objects.filter(pk=store.pk).update(**update_data)
