import os
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data
from api.utils.scraper_utils.get_aldi_categories import get_aldi_categories

SCRAPE_BATCH_SIZE = 2

def run_aldi_scraper():
    print("--- Starting Aldi scraping process ---")

    try:
        aldi_company = Company.objects.get(name="aldi")
    except Company.DoesNotExist:
        print("Company 'aldi' not found in the database.")
        return

    stores = Store.objects.filter(company=aldi_company, is_active=True)
    if not stores.exists():
        print("No active Aldi stores found in the database.")
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:SCRAPE_BATCH_SIZE]

    raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
    os.makedirs(raw_data_path, exist_ok=True)
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
