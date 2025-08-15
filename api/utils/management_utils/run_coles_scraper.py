import os
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data
from api.utils.management_utils.get_coles_categories import get_coles_categories

SCRAPE_BATCH_SIZE = 2

def run_coles_scraper():
    print("--- Starting Coles scraping process ---")

    try:
        coles_company = Company.objects.get(name="coles")
    except Company.DoesNotExist:
        print("Company 'coles' not found in the database.")
        return

    stores = Store.objects.filter(company=coles_company, is_active=True)
    if not stores.exists():
        print("No active Coles stores found in the database.")
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:SCRAPE_BATCH_SIZE]

    categories = get_coles_categories()

    raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
    os.makedirs(raw_data_path, exist_ok=True)
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
