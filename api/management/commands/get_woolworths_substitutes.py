
import time
import os
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.substitution_utils import (
    get_woolworths_product_store_ids,
    fetch_substitutes_from_api,
    get_product_by_store_id,
    link_products_as_substitutes,
    load_progress,
    save_progress,
    print_progress,
    save_discovered_product,
)

PROGRESS_FILE = os.path.join(settings.BASE_DIR, 'api', 'data', 'woolworths_substitutes_progress.json')

class Command(BaseCommand):
    help = 'Finds and saves substitute products for Woolworths items with progress tracking.'

    def setup_session(self):
        """Creates and warms up a requests session."""
        self.stdout.write("Setting up and warming up session...")
        session = requests.Session()
        session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.woolworths.com.au",
            "referer": "https://www.woolworths.com.au/shop/browse/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        })
        try:
            session.get("https://www.woolworths.com.au/", timeout=60)
            self.stdout.write(self.style.SUCCESS("Session is ready."))
            return session
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"CRITICAL: Failed to warm up session. Error: {e}"))
            return None

    def handle(self, *args, **options):
        session = self.setup_session()
        if not session:
            return

        self.stdout.write(self.style.SUCCESS("Starting to fetch Woolworths substitutes..."))

        remaining_ids = load_progress(PROGRESS_FILE)
        if remaining_ids is None:
            self.stdout.write("No progress file found. Getting all Woolworths product IDs from scratch.")
            product_ids_to_check = get_woolworths_product_store_ids()
            if not product_ids_to_check:
                self.stderr.write("No active Woolworths products found to process.")
                return
            total_products = len(product_ids_to_check)
            completed_count = 0
        else:
            # This part of the logic needs to be more robust
            # We need the original total to calculate progress correctly.
            # For now, we'll just show progress on the remaining items.
            self.stdout.write(self.style.WARNING(f"Resuming from progress file. {len(remaining_ids)} products left to check."))
            product_ids_to_check = remaining_ids
            total_products = len(product_ids_to_check) # This is not the overall total, but for this session.
            completed_count = 0

        print_progress(completed_count, total_products)

        for product_id in list(product_ids_to_check):
            if product_id not in product_ids_to_check:
                continue

            try:
                substitute_data_list = fetch_substitutes_from_api(product_id, session)
                time.sleep(1)
            except (requests.exceptions.RequestException, ValueError) as e:
                self.stderr.write(f"\nAPI Error for {product_id}: {e}. Skipping.")
                time.sleep(5)
                continue

            # The original product is processed, so remove it from the set
            product_ids_to_check.remove(product_id)
            increment = 1

            original_product = get_product_by_store_id(product_id)
            if not original_product:
                # If we can't find the original product, just update progress and move on
                completed_count += increment
                print_progress(completed_count, total_products)
                save_progress(PROGRESS_FILE, product_ids_to_check)
                continue

            if substitute_data_list:
                for sub_data in substitute_data_list:
                    # sub_data is a dictionary of product details
                    sub_id = str(sub_data.get('Stockcode'))

                    if sub_id in product_ids_to_check:
                        product_ids_to_check.remove(sub_id)
                        increment += 1
                    
                    substitute_product = get_product_by_store_id(sub_id)
                    if substitute_product:
                        # Product exists in DB, link it
                        if substitute_product != original_product:
                            link_products_as_substitutes(original_product, substitute_product)
                    else:
                        # Product is not in DB, save it for later
                        save_discovered_product(sub_data)

            completed_count += increment
            print_progress(completed_count, total_products)
            save_progress(PROGRESS_FILE, product_ids_to_check)

        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        print_progress(total_products, total_products) # Show 100%
        self.stdout.write(self.style.SUCCESS("\nSuccessfully finished fetching and linking Woolworths substitutes."))
