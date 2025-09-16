import os
from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.database_updating_utils.load_db_from_archive import load_db_from_latest_archive
from api.database_updating_classes.exact_category_matcher import ExactCategoryMatcher
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator
from api.database_updating_classes.prefix_update_orchestrator import PrefixUpdateOrchestrator
from api.database_updating_classes.discovery_update_orchestrator import DiscoveryUpdateOrchestrator

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the discovered_stores directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument('--prefixes', action='store_true', help='Update brand prefixes from the prefix_inbox directory.')
        parser.add_argument('--archive', action='store_true', help='Flush DB and load data from the most recent archive.')
        parser.add_argument('--category-links', action='store_true', help='Run the automatic category linker.')

    def handle(self, *args, **options):
        if options['archive']:
            load_db_from_latest_archive(self)
            return
        
        if options['category_links']:
            matcher = ExactCategoryMatcher(self)
            matcher.run()
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
            orchestrator = DiscoveryUpdateOrchestrator(self)
            orchestrator.run()

        if run_products_processed:
            inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')
            if not os.path.exists(inbox_path):
                self.stdout.write(self.style.WARNING("Product inbox directory not found."))
            else:
                orchestrator = UpdateOrchestrator(self, inbox_path)
                orchestrator.run()
            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))