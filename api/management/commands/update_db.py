from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery
from api.utils.database_updating_utils.update_products_from_processed import update_products_from_processed
from api.utils.database_updating_utils.update_stores_from_archive import update_stores_from_archive

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the discovered_stores directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the processed_data directory.')
        parser.add_argument('--archive', action='store_true', help='Update stores from the company_data archive.')

    def handle(self, *args, **options):
        run_stores = options['stores']
        run_products = options['products']
        run_archive = options['archive']

        # Default behavior: run stores then products if no flags are specified
        if not any([run_stores, run_products, run_archive]):
            run_stores = True
            run_products = True

        if run_archive:
            self.stdout.write(self.style.SUCCESS('--- Running store update from archive ---'))
            update_stores_from_archive(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from archive complete ---'))

        if run_stores:
            self.stdout.write(self.style.SUCCESS('--- Running store update from discovery ---'))
            update_stores_from_discovery(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from discovery complete ---'))

        if run_products:
            self.stdout.write(self.style.SUCCESS('--- Running product update from processed data ---'))
            update_products_from_processed(self)
            self.stdout.write(self.style.SUCCESS('--- Product update from processed data complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))
