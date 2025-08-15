import os
import random
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data
from api.utils.management_utils.get_woolworths_categories import get_woolworths_categories

from api.utils.management_utils.get_company_by_name import get_company_by_name, get_active_stores_for_company

def run_woolworths_scraper(batch_size, raw_data_path):
    print("--- Starting Woolworths scraping process ---")

    woolworths_company = get_company_by_name("woolworths")
    if not woolworths_company:
        return

    stores = get_active_stores_for_company(woolworths_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

    categories = get_woolworths_categories()
    if not categories:
        print("Could not fetch Woolworths categories. Aborting.")
        return
    
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
