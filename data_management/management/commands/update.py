import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from data_management.utils.database_updating_utils.load_db_from_archive import load_db_from_latest_archive      
from data_management.database_updating_classes.product_updating.update_orchestrator import UpdateOrchestrator
from data_management.database_updating_classes.gs1_update_orchestrator import GS1UpdateOrchestrator
from data_management.database_updating_classes.discovery_update_orchestrator import DiscoveryUpdateOrchestrator
from data_management.database_updating_classes.category_link_update_orchestrator import CategoryLinkUpdateOrchestrator                  
from data_management.database_updating_classes.substitution_update_orchestrator import SubstitutionUpdateOrchestrator
from data_management.database_updating_classes.bargain_update_orchestrator import BargainUpdateOrchestrator
class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Update stores from the store_inbox directory.')
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument('--gs1', action='store_true', help='Update brand prefixes from the gs1_inbox directory.')
        parser.add_argument('--cat-links', action='store_true', help='Update category links from the category_links_inbox directory.')
        parser.add_argument('--subs', action='store_true', help='Update substitutions from the substitutions_inbox directory.')
        parser.add_argument('--bargains', action='store_true', help='Update bargains from the bargains_outbox directory.')
        parser.add_argument('--archive', action='store_true', help='Flush DB and load data from the most recent archive.')
        parser.add_argument('--relaxed-staleness', action='store_true', help='Use a relative 7-day window for store group comparisons, based on the latest scrape date in the DB.')

    def handle(self, *args, **options):
        if options['archive']:
            load_db_from_latest_archive(self)
            return
        
        run_stores_discovery = options['stores']
        run_products_processed = options['products']
        run_gs1 = options['gs1']
        run_category_links = options['cat_links']
        run_substitutions = options['subs']
        run_bargains = options['bargains']
        relaxed_staleness = options['relaxed_staleness']

        if not any([run_stores_discovery, run_products_processed, run_gs1, run_category_links, run_substitutions, run_bargains]):
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

        if run_gs1:
            orchestrator = GS1UpdateOrchestrator(self)
            orchestrator.run()

        if run_stores_discovery:
            orchestrator = DiscoveryUpdateOrchestrator(self)
            orchestrator.run()

        if run_products_processed:
            inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'product_inbox')

            def files_exist_in_inbox():
                if not os.path.exists(inbox_path):
                    return False
                for _, _, files in os.walk(inbox_path):
                    if any(f.endswith('.jsonl') for f in files):
                        return True
                return False

            error_counter = 0
            MAX_RESTARTS = 10

            while files_exist_in_inbox():
                if error_counter >= MAX_RESTARTS:
                    self.stderr.write(self.command.style.ERROR(
                        f"Update command halted after {MAX_RESTARTS} consecutive restarts due to duplicate barcode errors."
                    ))
                    break
                
                try:
                    self.stdout.write(self.style.SUCCESS('Starting update orchestrator...'))
                    orchestrator = UpdateOrchestrator(self, relaxed_staleness=relaxed_staleness)
                    orchestrator.run()
                    # A successful run resets the counter
                    error_counter = 0 
                except IntegrityError as e:
                    if 'Duplicate entry' in str(e) and 'for key \'products_product.barcode\'' in str(e):
                        self.stdout.write(self.style.WARNING(
                            f"Duplicate barcode error detected. Restarting process... (Attempt {error_counter + 1}/{MAX_RESTARTS})"
                        ))
                        error_counter += 1
                        continue # Loop to the next attempt
                    else:
                        # It's a different integrity error, we should not loop.
                        self.stderr.write(self.command.style.ERROR(f"An unhandled IntegrityError occurred: {e}"))
                        raise # Re-raise and halt
                except Exception as e:
                    # Any other exception should also break the loop.
                    self.stderr.write(self.command.style.ERROR(f"An unexpected error occurred: {e}"))
                    raise # Re-raise and halt

            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))