import os
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data
from api.utils.management_utils.get_coles_categories import get_coles_categories

from api.utils.management_utils.get_company_by_name import get_company_by_name, get_active_stores_for_company

def run_coles_scraper(batch_size, raw_data_path):
    print("--- Starting Coles scraping process ---")

    coles_company = get_company_by_name("coles")
    if not coles_company:
        return

    stores = get_active_stores_for_company(coles_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

    categories = get_coles_categories()

    print(f"Data will be saved to: {raw_data_path}")

    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.name} ---")
        scrape_and_save_coles_data(
            company=coles_company.name,
            store_id=store.store_id,
            store_name=store.name,
            state=store.state,
            categories_to_fetch=categories,
            save_path=raw_data_path
        )
        store.last_scraped_products = timezone.now()
        store.save()

    print("\n--- Coles scraping process complete ---")
