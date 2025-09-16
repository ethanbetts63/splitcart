
import json
from companies.models import Company, Division, Store

class DiscoveryStoreProcessor:
    """
    Processes a single store discovery file and updates the database.
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
            self.command.stderr.write(self.command.style.ERROR(f"Could not read or parse {self.file_path}"))
            return None

        metadata = data.get('metadata', {})
        store_data = data.get('store_data', {})

        # Use 'company' key, not 'company_name'
        company_name = metadata.get('company')
        if not company_name or not store_data:
            return None

        company_obj = self._get_or_create_company(company_name)
        
        division_name = store_data.get('division')
        division_obj = None
        if division_name:
            division_obj = self._get_or_create_division(company_obj, division_name)

        self._get_or_create_store(company_obj, division_obj, store_data)
            
        return company_name

    def _get_or_create_company(self, company_name):
        company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
        return company_obj

    def _get_or_create_division(self, company_obj, division_name):
        division_obj, _ = Division.objects.get_or_create(company=company_obj, name__iexact=division_name, defaults={'name': division_name})
        return division_obj

    def _get_or_create_store(self, company_obj, division_obj, store_data):
        store_id = store_data.get('store_id')
        if not store_id:
            return

        # For companies like Woolworths, the store_id from scraping is just a number, 
        # but we want to store it with a prefix for uniqueness.
        if not ':' in store_id:
            prefix = company_obj.name.upper()[:3]
            store_id = f"{prefix}:{store_id}"

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
            'trading_hours': store_data.get('trading_hours'),
            'facilities': store_data.get('facilities')
        }

        store, created = Store.objects.update_or_create(
            store_id=store_id,
            company=company_obj,
            defaults=store_defaults
        )
        return store
