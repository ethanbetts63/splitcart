
import time
from django.core.management.base import BaseCommand
from api.utils.substitution_utils import (
    get_woolworths_product_store_ids,
    fetch_substitutes_from_api,
    get_product_by_store_id,
    link_products_as_substitutes,
)

class Command(BaseCommand):
    help = 'Finds and saves substitute products for Woolworths items using utility functions.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to fetch Woolworths substitutes...")

        product_ids_to_check = get_woolworths_product_store_ids()
        if not product_ids_to_check:
            self.stderr.write("No active Woolworths products found to process.")
            return

        total_products = len(product_ids_to_check)
        self.stdout.write(f"Found {total_products} unique Woolworths products to check.")

        processed_count = 0
        # Create a copy of the set to iterate over, as we will be modifying the original set
        for product_id in list(product_ids_to_check):
            if product_id not in product_ids_to_check:
                # This product was already processed as a substitute for another product
                continue

            processed_count += 1
            self.stdout.write(f"({processed_count}/{total_products}) Checking product ID: {product_id}")

            original_product = get_product_by_store_id(product_id)
            if not original_product:
                product_ids_to_check.remove(product_id)
                continue

            # If the product already has substitutes, we can skip it and its known substitutes
            if original_product.substitute_goods.exists():
                self.stdout.write(f"  -> Product '{original_product.name}' already has substitutes. Skipping.")
                # Remove the main product from the check list
                product_ids_to_check.remove(product_id)
                # Remove all its known substitutes from the check list
                for sub_product in original_product.substitute_goods.all():
                    sub_price = sub_product.prices.filter(is_active=True).first()
                    if sub_price and sub_price.store_product_id in product_ids_to_check:
                        product_ids_to_check.remove(sub_price.store_product_id)
                continue

            # Fetch substitutes from the API
            substitute_ids = fetch_substitutes_from_api(product_id)
            if not substitute_ids:
                self.stdout.write(f"  -> No substitutes found for {product_id}.")
                product_ids_to_check.remove(product_id)
                time.sleep(1) # API delay
                continue

            self.stdout.write(f"  -> Found {len(substitute_ids)} potential substitutes.")

            # Process and link the substitutes
            for sub_id in substitute_ids:
                substitute_product = get_product_by_store_id(sub_id)
                if substitute_product and substitute_product != original_product:
                    link_products_as_substitutes(original_product, substitute_product)
                    self.stdout.write(f"    - Linked: '{original_product.name}' <-> '{substitute_product.name}'")

                    # Remove the substitute from the set to avoid redundant checks
                    if sub_id in product_ids_to_check:
                        product_ids_to_check.remove(sub_id)
            
            # Remove the original product from the set
            if product_id in product_ids_to_check:
                 product_ids_to_check.remove(product_id)

            time.sleep(1) # Respectful delay between API calls

        self.stdout.write(self.style.SUCCESS("Successfully finished fetching and linking Woolworths substitutes."))
