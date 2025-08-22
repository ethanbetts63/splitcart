from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.management_utils.get_company_by_name import get_company_by_name
from api.utils.management_utils.get_active_stores_for_company import get_active_stores_for_company

def run_iga_scraper(batch_size):
    print("--- Starting IGA scraping process ---")

    iga_company = get_company_by_name("Iga")
    if not iga_company:
        return

    stores = get_active_stores_for_company(iga_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.store_name} ---")
        store_name_slug = slugify(store.store_name.lower().replace('iga', '').replace('fresh', ''))
        success = scrape_and_save_iga_data(
            company=iga_company.name,
            store_id=store.store_id,
            retailer_store_id=store.retailer_store_id,
            store_name=store.store_name,
            store_name_slug=store_name_slug,
            state=store.state
        )
        if success:
            store.is_online_shopable = True
            store.last_scraped_products = timezone.now()
            print(f"    Successfully scraped. Marked '{store.store_name}' as online shopable.")
        else:
            store.is_online_shopable = False
            print(f"    Scrape failed. Marked '{store.store_name}' as not online shopable.")
        store.save()

    print("\n--- IGA scraping process complete ---")