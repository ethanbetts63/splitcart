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

        archive_dir = os.path.join('archive', 'company_data')
        os.makedirs(archive_dir, exist_ok=True)

        companies = Company.objects.all()

        for company in companies:
            company_slug = slugify(company.name) # Use slugify for a file-safe name
            company_data = {
                'metadata': {
                    'company_name': company.name,
                    'company_slug': company_slug, # Use the slugified name
                    'data_generation_date': datetime.now().isoformat()
                },
                'stores_by_division': {}
            }

            stores = Store.objects.filter(company=company).select_related('division')

            for store in stores:
                division_name = store.division.name if store.division else 'No Division'
                division_slug = slugify(division_name) if store.division else 'no-division' # Use slugify for division name

                if division_slug not in company_data['stores_by_division']:
                    company_data['stores_by_division'][division_slug] = {
                        'division_name': division_name,
                        'stores': []
                    }
                
                store_details = {
                    'store_id': store.store_id,
                    'name': store.name,
                    'is_active': store.is_active,
                    'phone_number': store.phone_number,
                    'address_line_1': store.address_line_1,
                    'address_line_2': store.address_line_2,
                    'suburb': store.suburb,
                    'state': store.state,
                    'postcode': store.postcode,
                    'latitude': str(store.latitude) if store.latitude is not None else None,
                    'longitude': str(store.longitude) if store.longitude is not None else None,
                    'trading_hours': store.trading_hours,
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
                company_data['stores_by_division'][division_slug]['stores'].append(store_details)
            
            output_file_path = os.path.join(archive_dir, f'{company_slug}.json')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully built {company_slug}.json'))

        self.stdout.write(self.style.SUCCESS('Finished building company JSON files.'))
