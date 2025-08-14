import time
import os
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
)

# Define the path for the progress file
PROGRESS_FILE = os.path.join(settings.BASE_DIR, 'api', 'data', 'woolworths_substitutes_progress.json')

class Command(BaseCommand):
    help = 'Finds and saves substitute products for Woolworths items with progress tracking.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting to fetch Woolworths substitutes..."))

        # Load progress or get the initial set of IDs
        remaining_ids = load_progress(PROGRESS_FILE)
        if remaining_ids is None:
            self.stdout.write("No progress file found. Getting all Woolworths product IDs from scratch.")
            product_ids_to_check = get_woolworths_product_store_ids()
            if not product_ids_to_check:
                self.stderr.write("No active Woolworths products found to process.")
                return
        else:
            self.stdout.write(self.style.WARNING(f"Resuming from progress file. {len(remaining_ids)} products left to check."))
            product_ids_to_check = remaining_ids

        total_products = len(product_ids_to_check)
        completed_count = 0

        # Initial progress print
        print_progress(completed_count, total_products)

        # Create a copy to iterate over as we modify the original set
        for product_id in list(product_ids_to_check):
            if product_id not in product_ids_to_check:
                continue # Already processed as a substitute

            original_product = get_product_by_store_id(product_id)
            if not original_product:
                product_ids_to_check.remove(product_id)
                completed_count += 1
                print_progress(completed_count, total_products)
                save_progress(PROGRESS_FILE, product_ids_to_check)
                continue

            # Skip products that already have substitutes
            if original_product.substitute_goods.exists():
                product_ids_to_check.remove(product_id)
                # Account for this product and all its substitutes being "completed"
                increment = 1 + original_product.substitute_goods.count()
                completed_count += increment
                for sub_product in original_product.substitute_goods.all():
                    sub_price = sub_product.prices.filter(is_active=True).first()
                    if sub_price and sub_price.store_product_id in product_ids_to_check:
                        product_ids_to_check.remove(sub_price.store_product_id)
                print_progress(completed_count, total_products)
                save_progress(PROGRESS_FILE, product_ids_to_check)
                continue

            # Fetch from API
            substitute_ids = fetch_substitutes_from_api(product_id)
            time.sleep(1) # Respectful delay

            # Remove the original product from the set regardless of outcome
            product_ids_to_check.remove(product_id)
            
            if not substitute_ids:
                completed_count += 1
            else:
                processed_subs = 0
                for sub_id in substitute_ids:
                    if sub_id in product_ids_to_check:
                        product_ids_to_check.remove(sub_id)
                        processed_subs += 1

                    substitute_product = get_product_by_store_id(sub_id)
                    if substitute_product and substitute_product != original_product:
                        link_products_as_substitutes(original_product, substitute_product)
                
                # Increment completed count by 1 (for the original) + number of new substitutes found
                completed_count += (1 + processed_subs)

            # Update progress on screen and in file
            print_progress(completed_count, total_products)
            save_progress(PROGRESS_FILE, product_ids_to_check)

        # Final cleanup
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        # Final progress message
        print_progress(total_products, total_products) # Show 100%
        self.stdout.write(self.style.SUCCESS("\nSuccessfully finished fetching and linking Woolworths substitutes."))