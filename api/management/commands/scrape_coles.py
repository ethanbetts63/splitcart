import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data

class Command(BaseCommand):
    help = 'Launches the Selenium scraper to fetch all pages of product data from coles.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles scraping process for test stores ---"))

        company_name = "coles"

        # Hardcoded list of Coles stores for testing
        stores_to_scrape = [
            {'store_name': 'Coles Alice Springs', 'store_id': '418'},
            {'store_name': 'Coles Goondiwindi', 'store_id': '4384'},
            {'store_name': 'Coles Chisholm', 'store_id': '858'},
            {'store_name': 'Coles Eden', 'store_id': '5697'},
            {'store_name': 'Coles Burnie', 'store_id': '7541'},
            {'store_name': 'Coles Warrnambool (lava St)', 'store_id': '7730'},
            {'store_name': 'Coles Port Lincoln', 'store_id': '440'},
            {'store_name': 'Coles Albany', 'store_id': '364'},
        ]

        categories = [
            "meat-seafood", "fruit-vegetables", "dairy-eggs-fridge", "bakery",
            "deli", "pantry", "dietary-world-foods", "chips-chocolates-snacks",
            "drinks", "frozen", "household", "health-beauty", "baby", "pet", "liquorland",
        ]
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")

        for store_info in stores_to_scrape:
            store_name = store_info['store_name']
            store_id = store_info['store_id']
            self.stdout.write(self.style.SUCCESS(f"\n--- Handing off to scraper for store: {store_name} ({store_id}) ---"))
            scrape_and_save_coles_data(company_name, store_name, categories, raw_data_path, store_id)

        self.stdout.write(self.style.SUCCESS("\n--- All Coles test stores scraped successfully ---"))
