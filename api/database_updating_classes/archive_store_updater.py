
import json
from companies.models import Company, Division, Store

class ArchiveStoreUpdater:
    """
    Processes a single company archive JSON file and updates the database with store information.
    """

    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None, 0

        metadata = data.get('metadata', {})
        company_name = metadata.get('company_name')
        if not company_name:
            return None, 0

        company_obj = self._get_or_create_company(company_name)
        total_stores_processed = 0

        if 'stores_by_division' in data:
            total_stores_processed = self._process_divisions(data, company_obj)
        elif 'stores_by_state' in data:
            total_stores_processed = self._process_states(data, company_obj)
            
        return company_name, total_stores_processed

    def _process_divisions(self, data, company_obj):
        """
        Processes stores organized by division.
        """
        total_stores_processed = 0
        stores_by_division = data.get('stores_by_division', {})
        for division_slug, division_data in stores_by_division.items():
            division_name = division_data.get('division_name')
            if not division_name:
                continue
            
            division_obj = self._get_or_create_division(company_obj, division_name)
            stores_by_state = division_data.get('stores_by_state', {})

            for state_slug, state_data in stores_by_state.items():
                stores = state_data.get('stores', [])
                for store_data in stores:
                    self._get_or_create_store(company_obj, division_obj, store_data)
                    total_stores_processed += 1
        return total_stores_processed

    def _process_states(self, data, company_obj):
        """
        Processes stores organized by state (no divisions).
        """
        total_stores_processed = 0
        stores_by_state = data.get('stores_by_state', {})
        for state_slug, state_data in stores_by_state.items():
            stores = state_data.get('stores', [])
            for store_data in stores:
                self._get_or_create_store(company_obj, None, store_data)
                total_stores_processed += 1
        return total_stores_processed

    def _get_or_create_company(self, company_name):
        """
        Gets or creates a company.
        """
        company_obj, created = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
        return company_obj

    def _get_or_create_division(self, company_obj, division_name):
        """
        Gets or creates a division for a company.
        """
        division_obj, created = Division.objects.get_or_create(company=company_obj, name__iexact=division_name, defaults={'name': division_name})
        return division_obj

    def _get_or_create_store(self, company_obj, division_obj, store_data):
        """
        Gets or creates a store.
        """
        store_id = store_data.get('store_id')
        if not store_id:
            return

        store_defaults = {
            'division': division_obj,
            'store_name': store_data.get('store_name'),
            'address_line_1': store_data.get('address_line_1'),
            'suburb': store_data.get('suburb'),
            'state': store_data.get('state'),
            'postcode': store_data.get('postcode'),
            'latitude': store_data.get('latitude'),
            'longitude': store_data.get('longitude'),
            'phone_number': store_data.get('phone_number'),
            'is_active': store_data.get('is_active', True),
            'retailer_store_id': store_data.get('retailer_store_id')
        }

        store, created = Store.objects.get_or_create(
            store_id=store_id,
            company=company_obj,
            defaults=store_defaults
        )

        if not created:
            # Update existing store
            for key, value in store_defaults.items():
                setattr(store, key, value)
            store.save()