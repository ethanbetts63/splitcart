from django.conf import settings
from django.utils import timezone
from api.scrapers.scrape_and_save_woolworths import scrape_and_save_woolworths_data
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories
from api.utils.management_utils.get_company_by_name import get_company_by_name
from api.utils.management_utils.get_active_stores_for_company import get_active_stores_for_company

def run_woolworths_scraper(batch_size):
    print("--- Starting Woolworths scraping process ---")

    woolworths_company = get_company_by_name("Woolworths")
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
    
    for store in stores_to_scrape:
        print(f"\n--- Handing off to scraper for store: {store.store_name} ---")
        scrape_and_save_woolworths_data(
            company=woolworths_company.name,
            state=store.state,
            stores=[{'store_name': store.store_name, 'store_id': store.store_id}],
            categories_to_fetch=categories
        )
        store.last_scraped_products = timezone.now()
        store.save()

    print("\n--- Woolworths scraping process complete ---")
