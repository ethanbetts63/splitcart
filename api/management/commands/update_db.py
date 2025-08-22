import os
import json
import time
from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery
from api.utils.database_updating_utils.update_stores_from_archive import update_stores_from_archive
from api.utils.database_updating_utils.update_products_from_archive import update_products_from_archive
from api.utils.database_updating_utils.batch_create_new_products import batch_create_new_products
from api.utils.database_updating_utils.batch_create_prices import batch_create_prices
from api.utils.database_updating_utils.batch_create_category_relationships import batch_create_category_relationships

def update_products_from_inbox(command):
    inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')

    if not os.path.exists(inbox_path):
        command.stdout.write(command.style.WARNING('Product inbox directory not found.'))
        return

    json_files = [f for f in os.listdir(inbox_path) if f.endswith('.json')]
    if not json_files:
        command.stdout.write(command.style.SUCCESS("No files in the inbox to process."))
        return

    command.stdout.write(f"Found {len(json_files)} files in the inbox to process.")

    consolidated_data = {}
    processed_files = []
    total_files = len(json_files)
    processed_count = 0

    for filename in json_files:
        processed_count += 1
        command.stdout.write(f'\r  Processing file {processed_count}/{total_files}...', ending='')
        file_path = os.path.join(inbox_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            product_details = data.get('product', {})
            metadata = data.get('metadata', {})
            
            key = product_details.get('normalized_name_brand_size')
            if not key:
                continue

            if key in consolidated_data:
                # Simple merge: last one wins. Could be improved.
                pass

            price_info = {
                'store_id': metadata.get('store_id'),
                'price': product_details.get('price_current'),
                'is_on_special': product_details.get('is_on_sale', False),
                'is_available': True,
                'store_product_id': product_details.get('store_product_id')
            }

            consolidated_data[key] = {
                'product_details': product_details,
                'price_history': [price_info],
                'category_paths': [product_details.get('category_path', [])],
                'company_name': metadata.get('company')
            }

            processed_files.append(file_path)

        except json.JSONDecodeError:
            command.stderr.write(command.style.ERROR(f'  Invalid JSON in {filename}. Skipping file.'))
            continue
        except Exception as e:
            command.stderr.write(command.style.ERROR(f'  An unexpected error occurred processing {filename}: {e}'))
            continue
    
    command.stdout.write('')

    if not consolidated_data:

        command.stdout.write(command.style.WARNING("No valid products to process after consolidation."))
        return

    command.stdout.write(f"Consolidated to {len(consolidated_data)} unique products.")

    try:
        with transaction.atomic():
            product_cache = batch_create_new_products(command, consolidated_data)
            batch_create_prices(command, consolidated_data, product_cache)
            batch_create_category_relationships(consolidated_data, product_cache)

        for file_path in processed_files:
            os.remove(file_path)
        command.stdout.write(command.style.SUCCESS(f'  Successfully processed and removed {len(processed_files)} files from the inbox.'))

    except Exception as e:
        command.stderr.write(command.style.ERROR(f'  An error occurred during the database update. Files will not be deleted. Error: {e}'))

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the discovered_stores directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument(
            '--archive', 
            nargs='*', 
            help='Update from archives. Can specify "stores" and/or "products". No args means both.'
        )

    def handle(self, *args, **options):
        run_stores_discovery = options['stores']
        run_products_processed = options['products']
        archive_options = options['archive']

        if not any([run_stores_discovery, run_products_processed, archive_options is not None]):
            run_stores_discovery = True
            run_products_processed = True

        if archive_options is not None:
            run_all_archives = len(archive_options) == 0
            run_stores_archive = 'stores' in archive_options or run_all_archives
            run_products_archive = 'products' in archive_options or run_all_archives

            if run_stores_archive:
                self.stdout.write(self.style.SQL_FIELD('--- Running store update from company archives ---'))
                update_stores_from_archive(self)
                self.stdout.write(self.style.SUCCESS('--- Store update from company archives complete ---'))
            
            if run_products_archive:
                self.stdout.write(self.style.SQL_FIELD('--- Running FAST product update from store archives ---'))
                update_products_from_archive(self)
                self.stdout.write(self.style.SUCCESS('--- Product update from store archives complete ---'))

        if run_stores_discovery:
            self.stdout.write(self.style.SQL_FIELD('--- Running store update from discovery ---'))
            update_stores_from_discovery(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from discovery complete ---'))

        if run_products_processed:
            self.stdout.write(self.style.SQL_FIELD('--- Running product update from inbox ---'))
            update_products_from_inbox(self)
            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))