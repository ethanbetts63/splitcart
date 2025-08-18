from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery
from api.utils.database_updating_utils.update_products_from_processed import update_products_from_processed
from api.utils.database_updating_utils.update_stores_from_archive import update_stores_from_archive
# from api.utils.database_updating_utils.update_products_from_store_archives import update_products_from_store_archives
from api.utils.database_updating_utils.from_archive import perform_fast_update_from_archive

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the discovered_stores directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the processed_data directory.')
        parser.add_argument(
            '--archive', 
            nargs='*', 
            help='Update from archives. Can specify "stores" and/or "products". No args means both.'
        )

    def handle(self, *args, **options):
        run_stores_discovery = options['stores']
        run_products_processed = options['products']
        archive_options = options['archive']

        # Default behavior: run stores then products if no flags are specified
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
                # update_products_from_store_archives(self) # --- OLD SLOW METHOD
                perform_fast_update_from_archive(self) # +++ NEW FAST METHOD
                self.stdout.write(self.style.SUCCESS('--- Product update from store archives complete ---'))

        if run_stores_discovery:
            self.stdout.write(self.style.SQL_FIELD('--- Running store update from discovery ---'))
            update_stores_from_discovery(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from discovery complete ---'))

        if run_products_processed:
            self.stdout.write(self.style.SQL_FIELD('--- Running product update from processed data ---'))
            update_products_from_processed(self)
            self.stdout.write(self.style.SUCCESS('--- Product update from processed data complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))
