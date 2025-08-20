from products.models import Price
from companies.models import Store

def batch_create_prices(command, consolidated_data: dict, product_cache: dict):
    """
    Pass 3: Create all price records in a single batch.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Pass 3: Batch creating prices ---"))
    prices_to_create = []
    skipped_products_count = 0
    store_cache = {str(store.store_id): store for store in Store.objects.all()}
    if not store_cache:
        command.stdout.write(command.style.WARNING("DEBUG: store_cache is empty. Exiting batch_create_prices."))
        return

    for key, data in consolidated_data.items():
        product_obj = product_cache.get(key)
        if not product_obj:
            skipped_products_count += 1
            continue

        for price_data in data['price_history']:
            store_obj = store_cache.get(str(price_data['store_id']))
            if not store_obj: continue
            price_to_use = price_data.get('price')
            if price_to_use is None: continue

            prices_to_create.append(Price(
                product=product_obj, store=store_obj, price=price_to_use,
                is_on_special=price_data.get('is_on_special', False),
                is_available=price_data.get('is_available', True), is_active=True))

    if prices_to_create:
        command.stdout.write(f"Creating {len(prices_to_create)} new price records...", ending='\r')
        Price.objects.bulk_create(prices_to_create, batch_size=1000)
        command.stdout.write("Bulk create for prices complete.")
    else:
        command.stdout.write("No new price records to create.")
    
    command.stdout.write(f"Skipped {skipped_products_count} products due to not being found in product_cache.")
