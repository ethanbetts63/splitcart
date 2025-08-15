import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from companies.models import Company, Store
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Builds company JSON files with stores grouped by division and state.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to build company JSON files...'))

        base_archive_dir = os.path.join('api', 'data', 'archive')
        company_data_dir = os.path.join(base_archive_dir, 'company_data')
        os.makedirs(company_data_dir, exist_ok=True)

        companies = Company.objects.prefetch_related('stores', 'stores__division').all()

        for company in companies:
            company_slug = slugify(company.name)
            company_data = {
                'metadata': {
                    'company_name': company.name,
                    'company_slug': company_slug,
                    'data_generation_date': datetime.now().isoformat(),
                    'total_stores': 0
                }
            }

            stores = company.stores.all()
            company_data['metadata']['total_stores'] = stores.count()

            # Check if the company has any stores with divisions
            has_divisions = stores.filter(division__isnull=False).exists()

            if has_divisions:
                company_data['stores_by_division'] = {}
                for store in stores:
                    division_slug = slugify(store.division.name) if store.division else 'no-division'
                    division_name = store.division.name if store.division else 'No Division'
                    
                    if division_slug not in company_data['stores_by_division']:
                        company_data['stores_by_division'][division_slug] = {
                            'division_name': division_name,
                            'total_stores': 0,
                            'stores_by_state': {}
                        }
                    
                    state = store.state or 'Unknown'
                    if state not in company_data['stores_by_division'][division_slug]['stores_by_state']:
                        company_data['stores_by_division'][division_slug]['stores_by_state'][state] = {
                            'total_stores': 0,
                            'stores': []
                        }
                    
                    store_details = self.get_store_details(store, company)
                    company_data['stores_by_division'][division_slug]['stores_by_state'][state]['stores'].append(store_details)
                    company_data['stores_by_division'][division_slug]['stores_by_state'][state]['total_stores'] += 1
                    company_data['stores_by_division'][division_slug]['total_stores'] += 1
            else:
                company_data['stores_by_state'] = {}
                for store in stores:
                    state = store.state or 'Unknown'
                    if state not in company_data['stores_by_state']:
                        company_data['stores_by_state'][state] = {
                            'total_stores': 0,
                            'stores': []
                        }
                    
                    store_details = self.get_store_details(store, company)
                    company_data['stores_by_state'][state]['stores'].append(store_details)
                    company_data['stores_by_state'][state]['total_stores'] += 1

            output_file_path = os.path.join(company_data_dir, f'{company_slug}.json')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully built {company_slug}.json'))

        self.stdout.write(self.style.SUCCESS('Finished building company JSON files.'))

    def get_store_details(self, store, company):
        store_details = {
            'store_id': store.store_id,
            'name': store.name
        }
        
        trading_hours_value = store.trading_hours
        if company.name == 'Woolworths' and isinstance(store.trading_hours, list):
            try:
                simplified_hours = [item['TradingHourForDisplay'] for item in store.trading_hours if 'TradingHourForDisplay' in item]
                if simplified_hours:
                    trading_hours_value = simplified_hours
            except (TypeError, KeyError):
                pass

        fields_to_check = {
            'is_active': store.is_active,
            'phone_number': store.phone_number,
            'address_line_1': store.address_line_1,
            'address_line_2': store.address_line_2,
            'suburb': store.suburb,
            'state': store.state,
            'postcode': store.postcode,
            'latitude': str(store.latitude) if store.latitude is not None else None,
            'longitude': str(store.longitude) if store.longitude is not None else None,
            'trading_hours': trading_hours_value,
            'facilities': store.facilities,
            'is_trading': store.is_trading,
            'last_updated': store.last_updated.isoformat() if store.last_updated else None,
            'retailer_store_id': store.retailer_store_id,
            'email': store.email,
            'online_shop_url': store.online_shop_url,
            'store_url': store.store_url,
            'ecommerce_url': store.ecommerce_url,
            'record_id': store.record_id,
            'status': store.status,
            'store_type': store.store_type,
            'site_id': store.site_id,
            'category_hierarchy_id': store.category_hierarchy_id,
            'shopping_modes': store.shopping_modes,
            'available_customer_service_types': store.available_customer_service_types,
            'alcohol_availability': store.alcohol_availability,
        }

        for key, value in fields_to_check.items():
            if value is not None and value != "" and value != []:
                store_details[key] = value
        
        return store_details
