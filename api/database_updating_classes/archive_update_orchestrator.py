
import os
from django.conf import settings
from .store_updater import StoreUpdater
from .product_updater import ProductUpdater

class ArchiveUpdateOrchestrator:
    """
    Orchestrates the database update process from the archive files.
    """

    def __init__(self, command):
        self.command = command
        self.company_archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'company_data')
        self.store_archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'store_data')

    def run(self, update_stores=False, update_products=False):
        """
        The main public method that orchestrates the update process.
        """
        if update_stores:
            self._update_stores()
        
        if update_products:
            self._update_products()

    def _update_stores(self):
        """
        Updates the stores from the company archive files.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Store Update from Archive ---"))
        if not os.path.exists(self.company_archive_path):
            self.command.stdout.write(self.command.style.WARNING('Company data archive directory not found.'))
            return

        for filename in os.listdir(self.company_archive_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.company_archive_path, filename)
            self.command.stdout.write(self.command.style.SQL_FIELD(f"Processing file: {filename}..."))
            
            updater = StoreUpdater(self.command, file_path)
            company_name, stores_processed = updater.run()
            
            if company_name:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {stores_processed} stores for {company_name}."))
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SQL_FIELD("--- Store Update from Archive Complete ---"))

    def _update_products(self):
        """
        Updates the products from the store archive files.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD('--- Running FAST product update from store archives ---'))
        updater = ProductUpdater(self.command, self.store_archive_path)
        updater.run()
        self.command.stdout.write(self.command.style.SUCCESS('--- Product update from store archives complete ---'))
