import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data
from api.utils.management_utils.create_store_slug_aldi import create_store_slug_aldi

class Command(BaseCommand):
    """
    This Django management command initiates the scraping process for specific ALDI stores.
    """
    help = 'Launches the scraper to fetch all product data from specified ALDI stores.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting ALDI scraping process ---"))

        company_name = "aldi"
        
        # Hardcoded list of Perth ALDI stores to be scraped.
        # The 'store_id' is the 'servicePoint' ID from the API.
        stores_to_scrape = [
            {'store_name': create_store_slug_aldi('Yokine'), 'store_id': 'G075'},
            {'store_name': create_store_slug_aldi('Innaloo'), 'store_id': 'G090'},
            {'store_name': create_store_slug_aldi('Mirrabooka'), 'store_id': 'G049'},
            {'store_name': create_store_slug_aldi('Karrinyup'), 'store_id': 'G092'},
            {'store_name': create_store_slug_aldi('Inglewood'), 'store_id': 'G094'},
            {'store_name': create_store_slug_aldi('Warwick'), 'store_id': 'G087'},
            {'store_name': create_store_slug_aldi('Morley'), 'store_id': 'G066'},
            {'store_name': create_store_slug_aldi('Madeley'), 'store_id': 'G088'},
            {'store_name': create_store_slug_aldi('Beechboro'), 'store_id': 'G093'},
            {'store_name': create_store_slug_aldi('Belmont'), 'store_id': 'G047'},
        ]
        
        categories = [
            ('lower-prices', '1588161425841179'), ('super-savers/super-savers', '1588161407991418'),
            ('limited-time-only', '1588161420755352'), ('fruits-vegetables', '950000000'),
            ('fruits-vegetables/fresh-fruits', '1111111152'), ('fruits-vegetables/fresh-vegetables', '1111111153'),
            ('fruits-vegetables/salads', '1111111154'), ('fruits-vegetables/prepared-vegetables', '1111111155'),
            ('fruits-vegetables/fresh-herbs', '1111111156'), ('meat-seafood', '940000000'),
            ('meat-seafood/beef', '1111111144'), ('meat-seafood/pork', '1111111145'),
            ('meat-seafood/poultry', '1111111146'), ('meat-seafood/sausage', '1111111147'),
            ('meat-seafood/seafood', '1111111148'), ('meat-seafood/lamb', '1111111149'),
            ('deli-chilled-meats', '930000000'), ('deli-chilled-meats/deli-meats', '1111111137'),
            ('deli-chilled-meats/dips-spreads', '1111111138'), ('deli-chilled-meats/antipasto', '1111111140'),
            ('deli-chilled-meats/lunch-box', '1111111141'), ('deli-chilled-meats/vegetarian-vegan', '1588161407775081'),
            ('dairy-eggs-fridge', '960000000'), ('dairy-eggs-fridge/milk', '1111111160'),
            ('dairy-eggs-fridge/long-life-milk', '1111111161'), ('dairy-eggs-fridge/eggs', '1111111162'),
            ('dairy-eggs-fridge/cheese', '1111111163'), ('dairy-eggs-fridge/creams-custards', '1111111165'),
            ('dairy-eggs-fridge/butter-margarine', '1111111166'), ('dairy-eggs-fridge/lunch-box', '1111111167'),
            ('dairy-eggs-fridge/desserts', '1588161408332096'), ('dairy-eggs-fridge/ready-to-eat-meals', '1588161408332097'),
            ('dairy-eggs-fridge/yoghurt', '1111111164'), ('dairy-eggs-fridge/meal-kits', '1588161424169216'),
            ('pantry', '970000000'), ('pantry/jams-spreads', '1111111170'), ('pantry/canned-food', '1111111171'),
            ('pantry/oils-vinegars', '1111111172'), ('pantry/sauces', '1111111173'),
            ('pantry/herbs-spices', '1111111174'), ('pantry/tea-coffee-hot-chocolate', '1111111175'),
            ('pantry/stocks-gravy', '1111111176'), ('pantry/condiments-dressings', '1111111178'),
            ('pantry/pasta-rice-grains', '1111111179'), ('pantry/cereals-muesli', '1111111180'),
            ('pantry/confectionery', '1111111181'), ('pantry/crackers-crisp-breads', '1111111182'),
            ('pantry/chips-corn-chips-other', '1111111183'), ('pantry/biscuit-cookies', '1111111184'),
            ('pantry/lunch-box', '1111111185'), ('pantry/dried-fruits-nuts-jerky', '1111111186'),
            ('pantry/health-foods', '1111111187'), ('pantry/soups-noodles', '1111111188'),
            ('pantry/baking', '1588161407775080'), ('pantry/meal-kits', '1588161424169215'),
            ('bakery', '920000000'), ('bakery/muffins-cakes-other', '1111111131'),
            ('bakery/sliced-breads', '1111111132'), ('bakery/speciality-breads-rolls', '1111111133'),
            ('freezer', '980000000'), ('freezer/chips-wedges', '1111111191'),
            ('freezer/frozen-fruit-vegetables', '1111111192'), ('freezer/ice-cream-snacks', '1111111193'),
            ('freezer/ice-cream-tubs', '1111111194'), ('freezer/frozen-desserts', '1111111195'),
            ('freezer/frozen-pizzas', '1111111196'), ('freezer/frozen-meat-seafood', '1111111197'),
            ('freezer/frozen-ready-meals', '1111111198'), ('freezer/frozen-party-food-snacks', '1111111199'),
            ('drinks', '1000000000'), ('drinks/soft-drinks', '1111111207'),
            ('drinks/juices-cordials', '1111111208'), ('drinks/water', '1111111209'),
            ('drinks/sports-energy', '1111111210'), ('drinks/tea-coffee-hot-chocolate', '1111111211'),
            ('drinks/flavoured-milk', '1111111212'), ('drinks/iced-tea-kombucha', '1588161408332099'),
            ('health-beauty', '1040000000'), ('health-beauty/vitamins-sports-nutrition', '1111111240'),
            ('health-beauty/sun-skin-care', '1111111241'), ('health-beauty/shower-bath-care', '1111111242'),
            ('health-beauty/period-care', '1111111243'), ('health-beauty/personal-care-hygiene', '1111111244'),
            ('health-beauty/first-aid-medicinal', '1111111245'), ('health-beauty/cosmetics', '1111111246'),
            ('health-beauty/dental-care', '1111111247'), ('health-beauty/hair-care', '1111111248'),
            ('health-beauty/hair-removal', '1111111249'), ('baby', '1030000000'),
            ('baby/baby-nappies-wipes', '1111111234'), ('baby/baby-food', '1111111236'),
            ('cleaning-household', '1050000000'), ('cleaning-household/laundry', '1111111252'),
            ('cleaning-household/cleaning', '1111111253'), ('cleaning-household/bathroom', '1111111254'),
            ('cleaning-household/kitchen', '1111111255'), ('cleaning-household/pest-control', '1111111256'),
            ('cleaning-household/home-essentials', '1111111258'),
            ('cleaning-household/toilet-paper-tissues-paper-towels', '1111111260'),
            ('cleaning-household/air-fresheners-fragrances', '1111111262'), ('pets', '1020000000'),
            ('pets/cat-kitten', '1111111227'), ('pets/dogs-puppy', '1111111228'),
            ('pets/birds', '1111111229'), ('pets/fish', '1111111230'), ('pets/small-pets', '1111111231'),
            ('liquor', '1010000000'), ('liquor/beer', '1111111216'), ('liquor/cider', '1111111217'),
            ('liquor/white-wine', '1111111218'), ('liquor/red-wine', '1111111219'),
            ('liquor/rose', '1111111220'), ('liquor/sparkling-champagne', '1111111221'),
            ('liquor/spirits', '1111111222'), ('liquor/premixed', '1111111223'),
            ('snacks-confectionery', '1588161408332087'), ('snacks-confectionery/confectionery', '1588161408332088'),
            ('snacks-confectionery/chips-corn-chips-other', '1588161408332089'),
            ('snacks-confectionery/dried-fruits-nuts-jerky', '1588161408332090'),
            ('snacks-confectionery/biscuit-cookies', '1588161408332091'), ('front-of-store', '1588161408332092'),
            ('front-of-store/shopping-bags-token', '1588161408332093'), ('front-of-store/flowers', '1588161408332095'),
        ]
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")
        
        # Loop through each store and call the scraper
        for store in stores_to_scrape:
            self.stdout.write(self.style.SUCCESS(f"\n--- Handing off to scraper for store: {store['store_name']} ---"))
            scrape_and_save_aldi_data(
                company=company_name,
                store_name=store['store_name'],
                store_id=store['store_id'],
                categories_to_fetch=categories,
                save_path=raw_data_path
            )

        self.stdout.write(self.style.SUCCESS("\n--- ALDI scraping process complete ---"))
