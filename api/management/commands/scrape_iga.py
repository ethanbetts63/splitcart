import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga
class Command(BaseCommand):
    """
    This Django management command initiates the scraping process for IGA stores.
    """
    help = 'Launches the scraper to fetch all product data from specified IGA stores.'

    def handle(self, *args, **options):
        """
        Main execution method for the command.
        """
        self.stdout.write(self.style.SUCCESS("--- Starting IGA scraping process ---"))

        company_name = "iga"

        # The hardcoded list of Perth IGA stores to be scraped.
        stores_to_scrape = [
            {'store_name': create_store_slug_iga('Darwin City IGA X-press'), 'store_id': '17656'},
            {'store_name': create_store_slug_iga('Nollamara IGA'), 'store_id': '48742'},
            {'store_name': create_store_slug_iga('Stirling Fresh IGA'), 'store_id': '48276'},
            {'store_name': create_store_slug_iga('Tucker Fresh IGA Morris'), 'store_id': '52119'},
            {'store_name': create_store_slug_iga('Balga IGA'), 'store_id': '48102'},
            {'store_name': create_store_slug_iga('Doubleview Fresh IGA'), 'store_id': '48221'},
            {'store_name': create_store_slug_iga('East Perth IGA'), 'store_id': '48108'},
            {'store_name': create_store_slug_iga('Tucker Fresh IGA Carine'), 'store_id': '48131'},
            {'store_name': create_store_slug_iga('IGA Local Grocer Bayswater'), 'store_id': '48262'},
            {'store_name': create_store_slug_iga('Foodies Market Langley Park IGA'), 'store_id': '251695'},
            {'store_name': create_store_slug_iga('The Market Place Ballajura IGA'), 'store_id': '48274'},
        ]
        
        self.stdout.write(f"Found {len(stores_to_scrape)} IGA store(s) to scrape.")

        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")
        
        self.stdout.write("Handing off to the scraper function...")
        scrape_and_save_iga_data(company_name, stores_to_scrape, raw_data_path)

        self.stdout.write(self.style.SUCCESS("\n--- IGA scraping process complete ---"))

