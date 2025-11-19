from django.utils import timezone
from django.db import transaction
from products.models import Price
from datetime import datetime
from decimal import Decimal

class PriceManager:
    """
    Manages the creation, updating, and deletion of Price objects for a specific store.
    """
    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

    def process(self, raw_product_data, store):
        """
        Processes raw product data to create, update, or delete Price objects for the given store.
        """
        self.command.stdout.write(f"  - PriceManager: Processing prices for store {store.store_name}...")

        # Step 1: Reset was_price for all prices in this store
        self.command.stdout.write(f"    - Resetting was_price for all existing prices in store {store.store_name}...")
        Price.objects.filter(store=store).update(was_price=None)

        store_price_cache = self.caches['prices_by_store'].get(store.id, {})
        hash_to_pk_cache = store_price_cache.get('hash_to_pk', {})
        product_id_to_pk_cache = store_price_cache.get('product_id_to_pk', {})

        prices_to_create = []
        prices_to_update = []
        seen_hashes = set()
        
        # Get the scraped_date from the metadata of the first product in the consolidated data
        scraped_date_str = None
        if raw_product_data:
            scraped_date_str = raw_product_data[0].get('metadata', {}).get('scraped_date')

        scraped_datetime = None
        try:
            scraped_datetime = datetime.fromisoformat(scraped_date_str)
            # Make the datetime timezone-aware if it's naive
            if timezone.is_naive(scraped_datetime):
                scraped_datetime = timezone.make_aware(scraped_datetime)
            scraped_date = scraped_datetime.date()
        except (ValueError, TypeError):
            self.command.stderr.write(self.command.style.ERROR(f"    - Could not parse scraped_date: {scraped_date_str}. Cannot process prices."))
            return

        # Collect PKs of prices that will be updated to fetch their old prices
        pks_of_prices_to_update = []

        for data in raw_product_data:
            product_dict = data.get('product')
            if not product_dict:
                continue

            # Get the product_id from the shared product cache
            product_id = self.caches['products_by_norm_string'].get(product_dict.get('normalized_name_brand_size'))
            if not product_id:
                self.command.stderr.write(self.command.style.ERROR(f"    - Product (NNBS: {product_dict.get('normalized_name_brand_size')}) not found in cache. Skipping price."))
                continue

            # Get the price_hash from the file data
            current_price_hash = product_dict.get('price_hash')
            seen_hashes.add(current_price_hash)

            price_current_val = product_dict.get('price_current')
            unit_price_val = product_dict.get('unit_price')

            price_data = {
                'product_id': product_id, # Use product_id directly
                'store': store,
                'scraped_date': scraped_date,
                'price': Decimal(str(price_current_val)),
                'unit_price': Decimal(str(unit_price_val)) if unit_price_val is not None else None,
                'unit_of_measure': product_dict.get('unit_of_measure'),
                'per_unit_price_string': product_dict.get('per_unit_price_string'),
                'is_on_special': product_dict.get('is_on_special', False),
                'price_hash': current_price_hash,
                'was_price': None, # Initialize as None, set later for updates
                'save_amount': None, # Initialize as None, set later for updates
            }

            # Determine if create or update
            if current_price_hash in hash_to_pk_cache:
                # Price data is unchanged, do nothing
                pass
            else:
                # Price data has changed or is new
                if product_id in product_id_to_pk_cache: # Use product_id here
                    # Existing price for this product, but data changed -> UPDATE
                    price_pk = product_id_to_pk_cache[product_id] # Use product_id here
                    price_obj = Price(pk=price_pk, **price_data)
                    prices_to_update.append(price_obj)
                    pks_of_prices_to_update.append(price_pk)
                else:
                    # No existing price for this product -> CREATE
                    price_obj = Price(**price_data)
                    prices_to_create.append(price_obj)
        
        # Step 3: Get old prices for those that will be updated
        old_prices_map = {p.pk: p.price for p in Price.objects.filter(pk__in=pks_of_prices_to_update)}

        # Step 4: Set new was_price and calculate save_amount for prices to update
        for price_obj in prices_to_update:
            old_price = old_prices_map.get(price_obj.pk)
            if old_price is not None: # Should always be true for prices_to_update
                price_obj.was_price = old_price
                price_obj.save_amount = old_price - price_obj.price # Calculate save_amount
            else:
                price_obj.was_price = None 
                price_obj.save_amount = None

        # Identify prices to delete (delisted products)
        initial_hashes_in_db = set(hash_to_pk_cache.keys())
        hashes_to_delete = initial_hashes_in_db - seen_hashes
        pks_to_delete = [hash_to_pk_cache[h] for h in hashes_to_delete]

        if not prices_to_create and not prices_to_update and not pks_to_delete:
            self.command.stdout.write("    - No price changes to persist.")
            return

        # Persistence
        try:
            with transaction.atomic():
                if pks_to_delete:
                    self.command.stdout.write(f"    - Deleting {len(pks_to_delete)} delisted prices.")
                    Price.objects.filter(pk__in=pks_to_delete).delete()

                if prices_to_create:
                    self.command.stdout.write(f"    - Creating {len(prices_to_create)} new prices.")
                    Price.objects.bulk_create(prices_to_create, batch_size=500)

                if prices_to_update:
                    self.command.stdout.write(f"    - Updating {len(prices_to_update)} existing prices.")
                    update_fields = [
                        'scraped_date', 'price', 'was_price', 'unit_price',
                        'unit_of_measure', 'per_unit_price_string', 'is_on_special',
                        'price_hash', 'save_amount' # Add save_amount to update fields
                    ]
                    Price.objects.bulk_update(prices_to_update, update_fields, batch_size=500)
            
            # Update store's last_scraped date
            store.last_scraped = scraped_datetime
            store.save(update_fields=['last_scraped'])

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing prices: {e}"))
            raise
