import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data

class Command(BaseCommand):
    help = 'Launches the Selenium scraper to fetch all pages of product data from coles.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store-id',
            type=str,
            help='The ID of the specific Coles store to scrape (e.g., 4452).',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting coles scraping process ---"))

        store_id = options['store_id']
        company_name = "coles"
        
        # If a store_id is provided, the store_name can be the ID itself for folder naming.
        # Otherwise, it defaults to 'national'.
        store_name = store_id if store_id else "national"

        categories = [
            "meat-seafood", "fruit-vegetables", "dairy-eggs-fridge", "bakery",
            "deli", "pantry", "dietary-world-foods", "chips-chocolates-snacks",
            "drinks", "frozen", "household", "health-beauty", "baby", "pet", "liquorland",
        ]
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")

        self.stdout.write("Handing off to the scraper function...")
        # Pass the store_id to the scraper function.
        scrape_and_save_coles_data(company_name, store_name, categories, raw_data_path, store_id)

        self.stdout.write(self.style.SUCCESS("\n--- coles scraping process complete ---"))
