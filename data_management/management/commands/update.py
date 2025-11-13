import os
from django.conf import settings
from django.core.management.base import BaseCommand
from data_management.utils.database_updating_utils.load_db_from_archive import load_db_from_latest_archive      
from data_management.database_updating_classes.update_orchestrator import UpdateOrchestrator
from data_management.database_updating_classes.prefix_update_orchestrator import PrefixUpdateOrchestrator
from data_management.database_updating_classes.discovery_update_orchestrator import DiscoveryUpdateOrchestrator
from data_management.database_updating_classes.category_link_update_orchestrator import CategoryLinkUpdateOrchestrator                  
from data_management.database_updating_classes.substitution_update_orchestrator import SubstitutionUpdateOrchestrator
from data_management.database_updating_classes.bargain_update_orchestrator import BargainUpdateOrchestrator
from data_management.database_updating_classes.substitution_update_orchestrator import SubstitutionUpdateOrchestrator
from data_management.database_updating_classes.group_maintanance.group_maintenance_orchestrator import GroupMaintenanceOrchestrator
class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the store_inbox directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument('--prefixes', action='store_true', help='Update brand prefixes from the prefix_inbox directory.')
        parser.add_argument('--cat-links', action='store_true', help='Update category links from the category_links_inbox directory.')
        parser.add_argument('--subs', action='store_true', help='Update substitutions from the substitutions_inbox directory.')
        parser.add_argument('--bargains', action='store_true', help='Update bargains from the bargains_inbox directory.')
        parser.add_argument('--archive', action='store_true', help='Flush DB and load data from the most recent archive.')

    def handle(self, *args, **options):
        if options['archive']:
            load_db_from_latest_archive(self)
            return
        
        run_stores_discovery = options['stores']
        run_products_processed = options['products']
        run_prefixes = options['prefixes']
        run_category_links = options['cat_links']
        run_substitutions = options['subs']
        run_bargains = options['bargains']

        if not any([run_stores_discovery, run_products_processed, run_prefixes, run_category_links, run_substitutions, run_bargains]):
            run_stores_discovery = True
            run_products_processed = True

        if run_bargains:
            orchestrator = BargainUpdateOrchestrator(self)
            orchestrator.run()

        if run_substitutions:
            orchestrator = SubstitutionUpdateOrchestrator(self)
            orchestrator.run()

        if run_category_links:
            orchestrator = CategoryLinkUpdateOrchestrator(self)
            orchestrator.run()

        if run_prefixes:
            orchestrator = PrefixUpdateOrchestrator(self)
            orchestrator.run()

        if run_stores_discovery:
            orchestrator = DiscoveryUpdateOrchestrator(self)
            orchestrator.run()

        if run_products_processed:
            inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'product_inbox')
            print(f"Checking for inbox at: {inbox_path}")
            if not os.path.exists(inbox_path):
                self.stdout.write(self.style.WARNING("Product inbox directory not found."))
                self.stdout.write(self.style.WARNING("Product inbox directory not found."))
            else:
                orchestrator = UpdateOrchestrator(self, inbox_path)
                orchestrator.run()
            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

            # Run group maintenance tasks regardless of whether product files were processed
            group_maintenance_orchestrator = GroupMaintenanceOrchestrator(self)
            group_maintenance_orchestrator.run()

        self.stdout.write(self.style.SUCCESS('All update tasks finished.'))