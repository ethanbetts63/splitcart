from django.core.management.base import BaseCommand
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset
from api.utils.archiving_utils.construct_category_hierarchy import construct_category_hierarchy
from api.utils.archiving_utils.build_product_list import build_product_list
from api.utils.archiving_utils.save_json_file import save_json_file
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

        if not stores_to_process.exists():
            self.stdout.write(self.style.WARNING('No stores found for the given criteria.'))
            return

        total_stores = len(stores_to_process)
        self.stdout.write(f'Found {total_stores} store(s) to process...')

        for i, store in enumerate(stores_to_process):
            self.stdout.write(f'\n({i+1}/{total_stores}) Processing store: {store.name} ({store.store_id})...')

            # 1. Construct the category hierarchy
            category_hierarchy = construct_category_hierarchy(store)

            # 2. Build the list of products with price history
            product_list = build_product_list(store)

            # 3. Assemble the final dictionary for the JSON file
            store_data = {
                'metadata': {
                    'store_id': store.store_id,
                    'name': store.name,
                    'company_name': store.company.name,
                    'address_line_1': store.address_line_1,
                    'suburb': store.suburb,
                    'state': store.state,
                    'postcode': store.postcode,
                    'data_generation_date': datetime.now().isoformat(),
                    'category_hierarchy': category_hierarchy
                },
                'products': product_list
            }

            # 4. Save the JSON file
            company_slug = slugify(store.company.name)
            saved_path = save_json_file(company_slug, store.store_id, store_data)
            self.stdout.write(self.style.SUCCESS(f'  Successfully created file: {saved_path}'))

        self.stdout.write(self.style.SUCCESS('\nFinished building all store JSON files.'))
