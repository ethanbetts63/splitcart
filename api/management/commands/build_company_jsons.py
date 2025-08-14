import os
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from companies.models import Company, Store, Division
from django.utils.text import slugify # Import slugify

class Command(BaseCommand):
    help = 'Builds company JSON files with stores grouped by division.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to build company JSON files...'))

        # Define the base archive directory relative to the project root
        # This assumes the command is run from the project root (where manage.py is)
        base_archive_dir = os.path.join('api', 'data', 'archive')
        company_data_dir = os.path.join(base_archive_dir, 'company_data')
        os.makedirs(company_data_dir, exist_ok=True)

        companies = Company.objects.all()

        for company in companies:
            company_slug = slugify(company.name) # Use slugify for a file-safe name
            company_data = {
                'metadata': {
                    'company_name': company.name,
                    'company_slug': company_slug, # Use the slugified name
                    'data_generation_date': datetime.now().isoformat()
                },
                'stores_by_division': {},
                'stores_without_division': [] # New key for stores without a division
            }

            total_company_stores = 0 # Counter for total stores in the company

            stores = Store.objects.filter(company=company).select_related('division')

            for store in stores:
                total_company_stores += 1 # Increment total company stores

                if store.division: # If the store has a division
                    division_name = store.division.name
                    division_slug = slugify(division_name)

                    if division_slug not in company_data['stores_by_division']:
                        company_data['stores_by_division'][division_slug] = {
                            'division_name': division_name,
                            'total_stores_in_division': 0, # New counter for division stores
                            'stores': []
                        }
                    
                    company_data['stores_by_division'][division_slug]['total_stores_in_division'] += 1 # Increment division store count
                    target_store_list = company_data['stores_by_division'][division_slug]['stores']
                else: # If the store has no division
                    target_store_list = company_data['stores_without_division']
                
                store_details = {
                    'store_id': store.store_id,
                    'name': store.name
                }

                # --- Field Processing ---
                # Simplify Woolworths trading hours
                trading_hours_value = store.trading_hours
                if company.name == 'Woolworths' and isinstance(store.trading_hours, list):
                    try:
                        simplified_hours = [item['TradingHourForDisplay'] for item in store.trading_hours if 'TradingHourForDisplay' in item]
                        if simplified_hours:
                            trading_hours_value = simplified_hours
                    except (TypeError, KeyError):
                        pass # Keep original value if structure is not as expected

                # List of fields to check and add to the details if they have a value
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

                target_store_list.append(store_details)
            
            output_file_path = os.path.join(company_data_dir, f'{company_slug}.json')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully built {company_slug}.json'))

        self.stdout.write(self.style.SUCCESS('Finished building company JSON files.'))
