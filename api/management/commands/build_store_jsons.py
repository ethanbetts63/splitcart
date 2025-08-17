from django.core.management.base import BaseCommand
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset
from api.utils.archiving_utils.build_product_list import build_product_list
from api.utils.archiving_utils.save_json_file import save_json_file
from api.utils.archiving_utils.print_product_progress import print_product_progress
from django.utils.text import slugify
from datetime import datetime

class Command(BaseCommand):
    help = 'Builds store-specific JSON files with product and price data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Optional: The slug of a specific company to process.'
        )
        parser.add_argument(
            '--store',
            type=str,
            help='Optional: The ID of a specific store to process.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to build store JSON files...'))

        company_slug_arg = options.get('company')
        store_id_arg = options.get('store')

        stores_to_process = get_stores_queryset(company_slug_arg, store_id_arg)

        total_stores = stores_to_process.count()
        if total_stores == 0:
            self.stdout.write(self.style.WARNING('No stores found for the given criteria.'))
            return

        self.stdout.write(f'Found {total_stores} store(s) to process...')

        for i, store in enumerate(stores_to_process.iterator(), 1):
            self.stdout.write(f'\n({i}/{total_stores}) Processing store: {store.store_name} ({store.store_id})...')

            product_list = []
            products_processed_count = 0
            for product_data in build_product_list(store):
                products_processed_count += 1
                print_product_progress(products_processed_count)
                product_list.append(product_data)

            if products_processed_count == 0:
                self.stdout.write(self.style.WARNING(f'  Skipping store: No products found.'))
                continue
            
            self.stdout.write("") 

            store_data = {
                'metadata': {
                    'store_id': store.store_id,
                    'store_name': store.store_name,
                    'company_name': store.company.name,
                    'address_line_1': store.address_line_1,
                    'suburb': store.suburb,
                    'state': store.state,
                    'postcode': store.postcode,
                    'data_generation_date': datetime.now().isoformat(),
                },
                'products': product_list
            }

            company_slug = slugify(store.company.name)
            saved_path = save_json_file(company_slug, store.store_id, store_data)
            self.stdout.write(self.style.SUCCESS(f'  Successfully created file: {saved_path}'))

        self.stdout.write(self.style.SUCCESS('\nFinished building all store JSON files.'))
