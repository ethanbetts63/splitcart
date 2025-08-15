import os
from django.conf import settings
from django.utils import timezone
from companies.models import Company, Store
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.scraper_utils.get_iga_categories import get_iga_categories
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga

SCRAPE_BATCH_SIZE = 2

def run_iga_scraper():
    print("--- Starting IGA scraping process ---")

    try:
        iga_company = Company.objects.get(name="iga")
    except Company.DoesNotExist:
        print("Company 'iga' not found in the database.")
        return

    stores = Store.objects.filter(company=iga_company, is_active=True)
    if not stores.exists():
        print("No active IGA stores found in the database.")
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:SCRAPE_BATCH_SIZE]

    raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
    os.makedirs(raw_data_path, exist_ok=True)
    print(f"Data will be saved to: {raw_data_path}")

    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.name} ---")
        store_name_slug = create_store_slug_iga(store.name)
        scrape_and_save_iga_data(
            company=iga_company.name,
            store_id=store.store_id,
            store_name=store.name,
            store_name_slug=store_name_slug,
            state=store.state,
            save_path=raw_data_path
        )
        store.last_scraped_products = timezone.now()
        store.save()

    print("\n--- IGA scraping process complete ---")
