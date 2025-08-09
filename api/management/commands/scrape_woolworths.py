import os
import json
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data
from api.utils.management_utils.get_woolworths_categories import get_woolworths_categories

class Command(BaseCommand):
    help = 'Launches the scraper to fetch all pages of product data from specific Woolworths stores.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Woolworths scraping process ---"))

        company_name = "woolworths"

        # Load store data from JSON file
        stores_json_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'store_data', 'stores_woolworths', 'woolworths_stores_by_state.json')
        with open(stores_json_path, 'r') as f:
            stores_by_state_data = json.load(f)
        stores_by_state = stores_by_state_data['stores_by_state']

        categories = get_woolworths_categories()
        if not categories:
            self.stdout.write(self.style.ERROR("Could not fetch Woolworths categories. Aborting."))
            return
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")
        
        for state, stores in stores_by_state.items():
            if len(stores) > 2:
                stores_to_scrape = random.sample(stores, 2)
            else:
                stores_to_scrape = stores

            self.stdout.write(self.style.SUCCESS(f"\n--- Handing off to scraper for state: {state} ---"))
            scrape_and_save_woolworths_data(
                company=company_name,
                state=state,
                stores=stores_to_scrape,
                categories_to_fetch=categories,
                save_path=raw_data_path
            )

        self.stdout.write(self.style.SUCCESS("\n--- Woolworths scraping process complete ---"))
