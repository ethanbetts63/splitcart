import os
import json
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data

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

        categories = [
            ('fruit-veg', '1-E5BEE36E'), ('poultry-meat-seafood', '1_D5A2236'),
            ('meal-occasions', '1_8AD6702'), ('deli', '1_3151F6F'),
            ('dairy-eggs-fridge', '1_6E4F4E4'), ('bakery', '1_DEB537E'),
            ('lunch-box', '1_9E92C35'), ('freezer', '1_ACA2FC2'),
            ('snacks-confectionery', '1_717445A'), ('pantry', '1_39FD49C'),
            ('international-foods', '1_F229FBE'), ('drinks', '1_5AF3A0A'),
            ('beer-wine-spirits', '1_8E4DA6F'), ('beauty', '1_8D61DD6'),
            ('personal-care', '1_894D0A8'), ('health-wellness', '1_9851658'),
            ('cleaning-maintenance', '1_2432B58'), ('baby', '1_717A94B'),
            ('pet', '1_61D6FEB'), ('electronics', '1_B863F57'),
            ('home-lifestyle', '1_DEA3ED5'),
        ]
        
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
