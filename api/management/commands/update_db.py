import os
from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery
from api.utils.database_updating_utils.load_db_from_archive import load_db_from_latest_archive
from api.utils.database_updating_utils.update_category_links import update_category_links_from_inbox
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator
from api.database_updating_classes.prefix_update_orchestrator import PrefixUpdateOrchestrator

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the discovered_stores directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument('--prefixes', action='store_true', help='Update brand prefixes from the prefix_inbox directory.')
        parser.add_argument('--archive', action='store_true', help='Flush DB and load data from the most recent archive.')
        parser.add_argument('--category-links', action='store_true', help='Update category equivalence links from the inbox.')

    def handle(self, *args, **options):
        if options['archive']:
            load_db_from_latest_archive(self)
            return
        
        if options['category_links']:
            update_category_links_from_inbox(self)
            return

        run_stores_discovery = options['stores']
        run_products_processed = options['products']
        run_prefixes = options['prefixes']

        if not any([run_stores_discovery, run_products_processed, run_prefixes]):
            run_stores_discovery = True
            run_products_processed = True

        if run_prefixes:
            orchestrator = PrefixUpdateOrchestrator(self)
            orchestrator.run()

        if run_stores_discovery:
            self.stdout.write(self.style.SQL_FIELD('--- Running store update from discovery ---'))
            update_stores_from_discovery(self)
            self.stdout.write(self.style.SUCCESS('--- Store update from discovery complete ---'))

        if run_products_processed:
            inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')
            if not os.path.exists(inbox_path):
                self.stdout.write(self.style.WARNING("Product inbox directory not found."))
            else:
                orchestrator = UpdateOrchestrator(self, inbox_path)
                orchestrator.run()
            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))