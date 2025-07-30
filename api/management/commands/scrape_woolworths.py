import os
from django.core.management.base import BaseCommand
from django.conf import settings
# I've updated the function name to match the latest scraper version
from api.scrapers.woolworths_scraper import scrape_and_save_woolworths_data

class Command(BaseCommand):
    help = 'Launches the scraper to fetch all pages of product data from Woolworths.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Woolworths scraping process ---"))

        # Define the categories you want to scrape here.
        categories = [
            ('electronics', '1_B863F57'),
            ('fruit-veg', '1_3A21EEE'),
        ]
        
        # Define the path to the raw_data directory
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        
        # Ensure the directory exists
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")

        # --- THE FIX ---
        # Call the scraper tool and pass it the save path.
        # The scraper will now handle all the logic and file saving.
        scrape_and_save_woolworths_data(categories, raw_data_path)

        self.stdout.write(self.style.SUCCESS("\n--- Woolworths scraping process complete ---"))
