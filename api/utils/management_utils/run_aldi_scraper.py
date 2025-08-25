import os
from django.conf import settings
from django.utils import timezone
from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data
from api.utils.management_utils.get_company_by_name import get_company_by_name
from api.utils.management_utils.get_active_stores_for_company import get_active_stores_for_company

def run_aldi_scraper(command, batch_size):

    aldi_company = get_company_by_name("Aldi")
    if not aldi_company:
        return

    stores = get_active_stores_for_company(aldi_company)
    if not stores:
        return

    # Prioritize stores that have never been scraped, then the least recently scraped
    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

    for store in stores_to_scrape:
        scrape_and_save_aldi_data(
            command,
            company=aldi_company.name,
            store_name=store.store_name,
            store_id=store.store_id,
            state=store.state
        )
        store.last_scraped_products = timezone.now()
        store.save()
