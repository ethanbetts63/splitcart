from django.core.management.base import BaseCommand
from api.archivers.store_archiver import StoreArchiver
from api.archivers.product_archiver import ProductArchiver
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset

class Command(BaseCommand):
    help = 'Builds store and product archive files.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Build the store archives (from company data).')
        parser.add_argument('--products', action='store_true', help='Build the product archives (for each store).')
        parser.add_argument('--company', type=str, help='Slug of a specific company to process for products.')
        parser.add_argument('--store', type=str, help='ID of a specific store to process for products.')


    def handle(self, *args, **options):
        run_stores = options['stores']
        run_products = options['products']
        company_slug = options['company']
        store_id = options['store']

        if not run_stores and not run_products:
            run_stores = True
            run_products = True

        if run_stores:
            archiver = StoreArchiver(self)
            archiver.run()
        
        if run_products:
            self.build_product_archives(company_slug, store_id)

        self.stdout.write(self.style.SUCCESS('Archiving process complete.'))

    def build_product_archives(self, company_slug, store_id):
        self.stdout.write(self.style.SUCCESS('Starting to build store JSON files...'))

        stores_queryset = get_stores_queryset(company_slug, store_id)
        store_ids = list(stores_queryset.values_list('store_id', flat=True))

        total_stores = len(store_ids)
        if total_stores == 0:
            self.stdout.write(self.style.WARNING('No stores found for the given criteria.'))
            return

        self.stdout.write(f'Found {total_stores} store(s) to process...\n')

        for i, store_id in enumerate(store_ids, 1):
            archiver = ProductArchiver(self, store_id)
            result = archiver.run()
            status = result.get('status')
            store_name = result.get('store_name', result.get('store_id', 'Unknown'))
            
            progress = f'({i}/{total_stores})'

            if status == 'success':
                products_found = result.get('products_found', 0)
                self.stdout.write(self.style.SUCCESS(f'{progress} Successfully processed {store_name} ({products_found} products): {result["path"]}'))
            elif status == 'skipped':
                self.stdout.write(self.style.WARNING(f'{progress} Skipped {store_name}: {result["reason"]}'))
            elif status == 'error':
                self.stdout.write(self.style.ERROR(f'{progress} Error processing store {store_name}: {result["error"]}'))

        self.stdout.write(self.style.SUCCESS('\nFinished building all store JSON files.'))