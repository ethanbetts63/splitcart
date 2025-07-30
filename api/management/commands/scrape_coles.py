import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.coles_scraper import fetch_coles_data

class Command(BaseCommand):
    help = 'Launches the Selenium scraper to fetch product data from Coles and saves it to raw_data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles scraping process ---"))

        # Define the categories you want to scrape here
        categories = [
            "fruit-vegetables",
            "meat-seafood",
            "bakery"
        ]
        
        self.stdout.write(f"Attempting to scrape {len(categories)} categories...")

        # Call the scraper tool to get the data
        # This will trigger the browser to open and the CAPTCHA prompt
        scraped_data_dict = fetch_coles_data(categories)

        if not scraped_data_dict:
            self.stdout.write(self.style.ERROR("Scraper returned no data. Process finished."))
            return

        # Define the path to the raw_data directory
        # Assumes your 'api' app is at the root of your project
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        
        # Ensure the directory exists
        os.makedirs(raw_data_path, exist_ok=True)
        
        self.stdout.write(self.style.SUCCESS(f"\nSaving {len(scraped_data_dict)} files to '{raw_data_path}'..."))

        # Get a timestamp for the filenames
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Loop through the returned data and save each category to a file
        for category_slug, json_data in scraped_data_dict.items():
            file_name = f"coles_{category_slug}_{timestamp}.json"
            file_path = os.path.join(raw_data_path, file_name)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                self.stdout.write(self.style.SUCCESS(f"  - Successfully saved {file_name}"))
            except IOError as e:
                self.stdout.write(self.style.ERROR(f"  - FAILED to save {file_name}. Error: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Coles scraping process complete ---"))
