import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data

class Command(BaseCommand):
    """
    This Django management command initiates the scraping process for IGA stores.
    """
    help = 'Launches the scraper to fetch all product data from specified IGA stores.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IGA scraping process ---"))

        company_name = "iga"
        stores_to_scrape = [
            {'store_name': 'east-victoria-park', 'store_id': '48264'},
            # Example of another store you found
            # {'store_name': 'another-store', 'store_id': '48274'},
        ]
        
        self.stdout.write(f"Found {len(stores_to_scrape)} IGA store(s) to scrape.")

        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")
        
        self.stdout.write("Handing off to the scraper function...")
        scrape_and_save_iga_data(company_name, stores_to_scrape, raw_data_path)

        self.stdout.write(self.style.SUCCESS("\n--- IGA scraping process complete ---"))
