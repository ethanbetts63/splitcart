import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data
from api.utils.management_utils.create_store_slug_woolworths import create_store_slug_woolworths

class Command(BaseCommand):
    help = 'Launches the scraper to fetch all pages of product data from specific Woolworths stores.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Woolworths scraping process ---"))

        company_name = "woolworths"

        # The 'store_id' is the 'StoreNo' from the API.
        stores_to_scrape = [
            {'store_name': create_store_slug_woolworths('Dianella'), 'store_id': '4366'},
            {'store_name': create_store_slug_woolworths('Mirrabooka'), 'store_id': '4373'},
            {'store_name': create_store_slug_woolworths('Noranda'), 'store_id': '4314'},
            {'store_name': create_store_slug_woolworths('Morley'), 'store_id': '4350'},
            {'store_name': create_store_slug_woolworths('Dog Swamp'), 'store_id': '4306'},
            {'store_name': create_store_slug_woolworths('Inglewood'), 'store_id': '4622'},
            {'store_name': create_store_slug_woolworths('Balcatta'), 'store_id': '4630'},
            {'store_name': create_store_slug_woolworths('Stirling Central'), 'store_id': '4319'},
            {'store_name': create_store_slug_woolworths('Mt Hawthorn'), 'store_id': '4346'},
            {'store_name': create_store_slug_woolworths('Highgate'), 'store_id': '4621'},
            {'store_name': create_store_slug_woolworths('Alexander Heights'), 'store_id': '4321'},
            {'store_name': create_store_slug_woolworths('Innaloo'), 'store_id': '4313'},
            {'store_name': create_store_slug_woolworths('Beechboro'), 'store_id': '4384'},
            {'store_name': create_store_slug_woolworths('Warwick'), 'store_id': '4379'},
            {'store_name': create_store_slug_woolworths('Murray Street'), 'store_id': '4365'},
            {'store_name': create_store_slug_woolworths('St Georges Terrace'), 'store_id': '4301'},
            {'store_name': create_store_slug_woolworths('Subiaco Square'), 'store_id': '4392'},
            {'store_name': create_store_slug_woolworths('Belmont'), 'store_id': '4348'},
            {'store_name': create_store_slug_woolworths('Ballajura Central'), 'store_id': '4339'},
            {'store_name': create_store_slug_woolworths('Bennett Springs'), 'store_id': '4155'},
            {'store_name': create_store_slug_woolworths('Karrinyup'), 'store_id': '4371'},
            {'store_name': create_store_slug_woolworths('Kingsway'), 'store_id': '4327'},
            {'store_name': create_store_slug_woolworths('Perth Airport'), 'store_id': '4389'},
            {'store_name': create_store_slug_woolworths('Floreat'), 'store_id': '4359'},
            {'store_name': create_store_slug_woolworths('Victoria Park'), 'store_id': '4333'},
        ]

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
        
        for store in stores_to_scrape:
            self.stdout.write(self.style.SUCCESS(f"\n--- Handing off to scraper for store: {store['store_name']} ---"))
            scrape_and_save_woolworths_data(
                company=company_name,
                store_name=store['store_name'],
                store_id=store['store_id'],
                categories_to_fetch=categories,
                save_path=raw_data_path
            )

        self.stdout.write(self.style.SUCCESS("\n--- Woolworths scraping process complete ---"))
