from django.conf import settings
from django.utils import timezone
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga
from api.utils.management_utils.get_company_by_name import get_company_by_name
from api.utils.management_utils.get_active_stores_for_company import get_active_stores_for_company

def run_iga_scraper(batch_size, raw_data_path):
    print("--- Starting IGA scraping process ---")

    iga_company = get_company_by_name("Iga")
    if not iga_company:
        return

    stores = get_active_stores_for_company(iga_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

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