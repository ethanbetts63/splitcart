import os
from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator
from api.database_updating_classes.archive_update_orchestrator import ArchiveUpdateOrchestrator

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

            orchestrator = ArchiveUpdateOrchestrator(self)
            orchestrator.run(update_stores=run_stores_archive, update_products=run_products_archive)

        if run_stores_discovery:
            self.stdout.write(self.style.SQL_FIELD('--- Running store update from discovery ---'))
            update_stores_from_discovery(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from discovery complete ---'))

        if run_products_processed:
            self.stdout.write(self.style.SQL_FIELD('--- Running product update from inbox (OOP Refactor) ---'))
            inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')
            if not os.path.exists(inbox_path):
                self.stdout.write(self.style.WARNING("Product inbox directory not found."))
            else:
                orchestrator = UpdateOrchestrator(self, inbox_path)
                orchestrator.run()
            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))