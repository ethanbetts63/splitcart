
import os
from django.conf import settings
from .discovery_store_updater import DiscoveryStoreUpdater

class DiscoveryUpdateOrchestrator:
    """
    Orchestrates the database update process from the discovered stores directory.
    """

    def __init__(self, command):
        self.command = command
        self.discovered_stores_path = os.path.join(settings.BASE_DIR, 'data_managementa_management', 'data', 'discovered_stores')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Store Update from Discovery ---"))
        if not os.path.exists(self.discovered_stores_path):
            self.command.stdout.write(self.command.style.WARNING('Discovered stores directory not found.'))
            return

        for filename in os.listdir(self.discovered_stores_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.discovered_stores_path, filename)
            
            updater = DiscoveryStoreUpdater(self.command, file_path)
            company_name, stores_processed = updater.run()
            
            if company_name:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {stores_processed} stores for {company_name}."))
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SQL_FIELD("--- Store Update from Discovery Complete ---"))
