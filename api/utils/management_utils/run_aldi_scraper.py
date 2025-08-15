import os
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data
from api.utils.scraper_utils.get_aldi_categories import get_aldi_categories

from api.utils.management_utils.get_company_by_name import get_company_by_name, get_active_stores_for_company

def run_aldi_scraper(batch_size, raw_data_path):
    print("--- Starting Aldi scraping process ---")

    aldi_company = get_company_by_name("aldi")
    if not aldi_company:
        return

    stores = get_active_stores_for_company(aldi_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

    print(f"Data will be saved to: {raw_data_path}")

    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.name} ---")
        scrape_and_save_aldi_data(
            company=aldi_company.name,
            store_name=store.name,
            store_id=store.store_id,
            state=store.state,
            save_path=raw_data_path
        )
        store.last_scraped_products = timezone.now()
        store.save()

    print("\n--- Aldi scraping process complete ---")
