import os
import random
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories

SCRAPE_BATCH_SIZE = 2

def run_woolworths_scraper():
    print("--- Starting Woolworths scraping process ---")

    try:
        woolworths_company = Company.objects.get(name="woolworths")
    except Company.DoesNotExist:
        print("Company 'woolworths' not found in the database.")
        return

    stores = Store.objects.filter(company=woolworths_company, is_active=True)
    if not stores.exists():
        print("No active Woolworths stores found in the database.")
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:SCRAPE_BATCH_SIZE]

    categories = get_woolworths_categories()
    if not categories:
        print("Could not fetch Woolworths categories. Aborting.")
        return
    
    raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
    os.makedirs(raw_data_path, exist_ok=True)
    print(f"Data will be saved to: {raw_data_path}")
    
    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.name} ---")
        scrape_and_save_woolworths_data(
            company=woolworths_company.name,
            state=store.state,
            stores=[{'store_name': store.name, 'store_id': store.store_id}],
            categories_to_fetch=categories,
            save_path=raw_data_path
        )
        store.last_scraped_products = timezone.now()
        store.save()

    print("\n--- Woolworths scraping process complete ---")

def run_coles_scraper():
    print("Coles scraper not implemented yet.")

def run_aldi_scraper():
    print("Aldi scraper not implemented yet.")

def run_iga_scraper():
    print("Iga scraper not implemented yet.")
