import os
from django.core.management.base import BaseCommand
from django.conf import settings
# Note the new function name we are importing
from api.scrapers.coles_scraper import scrape_and_save_coles_data

class Command(BaseCommand):
    help = 'Launches the Selenium scraper to fetch all pages of product data from Coles.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles scraping process ---"))

        # Define the categories you want to scrape here
        categories = [
            "fruit-vegetables",
            "meat-seafood",
        ]
        
        # Define the path to the raw_data directory
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        
        # Ensure the directory exists
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")

        # Call the scraper tool. It will handle everything else.
        scrape_and_save_coles_data(categories, raw_data_path)

        self.stdout.write(self.style.SUCCESS("\n--- Coles scraping process complete ---"))
