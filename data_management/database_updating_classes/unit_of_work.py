from django.db import transaction
from datetime import datetime
from products.models import Product, Price, ProductBrand
from companies.models import Store # Changed from StoreGroup
from django.core.exceptions import ValidationError
from decimal import InvalidOperation
from .category_manager import CategoryManager

class UnitOfWork:
    def __init__(self, command, resolver=None):
        self.command = command
        self.resolver = resolver
        self.new_products_to_process = []
        self.products_to_update = set()
        self.brands_to_update = set()
        self.prices_to_upsert = []
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance, product_details, metadata):
        """
        Adds a new product instance along with its raw details for later processing.
        """
        self.new_products_to_process.append((product_instance, product_details, metadata))

    def add_price(self, product, store, product_details, metadata):
        scraped_date_str = metadata.get('scraped_date')
        price_value = product_details.get('price_current')

        if not scraped_date_str or not price_value:
            return

        try:
            scraped_date = datetime.strptime(scraped_date_str[:10], '%Y-%m-%d').date()
            
            price_data = {
                'product': product,
                'store': store,
                'scraped_date': scraped_date,
                'price': price_value,
                'was_price': product_details.get('price_was'),
                'unit_price': product_details.get('unit_price'),
                'unit_of_measure': product_details.get('unit_of_measure'),
                'per_unit_price_string': product_details.get('per_unit_price_string'),
                'is_on_special': product_details.get('is_on_special', False),
                'price_hash': product_details.get('price_hash'),
                'source': 'direct_scrape'
            }
            self.prices_to_upsert.append(price_data)

        except (ValidationError, InvalidOperation, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f'\nError preparing price data: {e}'))
            self.command.stderr.write(self.command.style.ERROR(f'Problematic product details: {product_details}'))
            return

    def add_for_update(self, instance):
        if isinstance(instance, Product):
            self.products_to_update.add(instance)
        elif isinstance(instance, ProductBrand):
            self.brands_to_update.add(instance)

    def _deduplicate_new_products(self, resolver):
        unique_new_products_with_details = []
        seen_barcodes = set()
        seen_normalized_strings = set()

        for product, details, metadata in self.new_products_to_process:
            if product.barcode and product.barcode in seen_barcodes:
                continue
            if product.normalized_name_brand_size and product.normalized_name_brand_size in seen_normalized_strings:
                continue
            
            unique_new_products_with_details.append((product, details, metadata))
            if product.barcode:
                seen_barcodes.add(product.barcode)
            if product.normalized_name_brand_size:
                seen_normalized_strings.add(product.normalized_name_brand_size)
        return unique_new_products_with_details

    def commit(self, consolidated_data, product_cache, resolver, store, initial_price_cache, is_full_sync):
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                unique_new_products_with_details = self._deduplicate_new_products(resolver)
                
                if unique_new_products_with_details:
                    new_products_list = [p for p, d, m in unique_new_products_with_details]
                    new_products_map_by_norm_string = {p.normalized_name_brand_size: (p, d, m) for p, d, m in unique_new_products_with_details}
                    
                    self.command.stdout.write(f"  - Creating {len(new_products_list)} truly unique new products.")
                    Product.objects.bulk_create(new_products_list, batch_size=500)

                    # Re-fetch the products to get their IDs
                    newly_created_products_with_ids = Product.objects.filter(
                        normalized_name_brand_size__in=new_products_map_by_norm_string.keys()
                    ).in_bulk(field_name='normalized_name_brand_size')

                    # Now that products are created and have IDs, add their prices to the upsert list
                    for norm_string, product_instance_with_id in newly_created_products_with_ids.items():
                        _, product_details, metadata = new_products_map_by_norm_string[norm_string]
                        self.add_price(product_instance_with_id, store, product_details, metadata)

                    # Refresh the product_cache with the newly created products (which now have IDs)
                    for norm_string, p in newly_created_products_with_ids.items():
                        product_cache[norm_string] = p

                # Stage 2: Upsert Price objects using hash-based comparison
                stale_price_ids = []
                if self.prices_to_upsert:
                    self.command.stdout.write(f"  - Processing {len(self.prices_to_upsert)} Price objects using hash comparison...")

                    # 1. Build lookup maps from the database cache
                    # Maps product_id to its existing price record ID
                    product_id_to_price_id_map = {p['product_id']: p['id'] for p in initial_price_cache}
                    # Maps a hash to its existing price record ID
                    existing_hashes_map = {p['price_hash']: p['id'] for p in initial_price_cache if p['price_hash']}
                    
                    prices_to_create = []
                    prices_to_update = []
                    seen_hashes = set()

                    # 2. Sort prices into 'create' or 'update' lists
                    total_prices = len(self.prices_to_upsert)
                    for i, price_data in enumerate(self.prices_to_upsert):
                        if (i + 1) % 500 == 0 or (i + 1) == total_prices:
                            self.command.stdout.write(f'\r    - Comparing prices: {i + 1}/{total_prices}', ending='')
                        
                        incoming_hash = price_data.get('price_hash')
                        if not incoming_hash:
                            continue # Should not happen, but good to be safe

                        seen_hashes.add(incoming_hash)

                        # If hash exists, price is unchanged. Skip it.
                        if incoming_hash in existing_hashes_map:
                            continue

                        # This price is either new or updated.
                        product_id = price_data['product'].id
                        if product_id in product_id_to_price_id_map:
                            # It's an UPDATE because the product already has a price record, but the hash is different.
                            price_id = product_id_to_price_id_map[product_id]
                            price_obj = Price(id=price_id, **price_data)
                            prices_to_update.append(price_obj)
                        else:
                            # It's a CREATE because the product does not have a price record.
                            prices_to_create.append(Price(**price_data))
                    self.command.stdout.write('') # Newline after progress bar

                    # 3. Perform bulk operations
                    if prices_to_create:
                        Price.objects.bulk_create(prices_to_create, batch_size=500)
                        self.command.stdout.write(f"  - Created {len(prices_to_create)} new Price objects.")

                    if prices_to_update:
                        update_fields = list(self.prices_to_upsert[0].keys())
                        update_fields.remove('product')
                        update_fields.remove('store')
                        Price.objects.bulk_update(prices_to_update, update_fields, batch_size=500)
                        self.command.stdout.write(f"  - Updated {len(prices_to_update)} existing Price objects.")

                    # 4. Identify stale prices for deletion
                    stale_hashes = set(existing_hashes_map.keys()) - seen_hashes
                    stale_price_ids = [existing_hashes_map[h] for h in stale_hashes]


                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store.company)

                # Stage 4: Update existing products
                if self.products_to_update:
                    update_fields = [
                        'barcode', 'url', 'image_url_pairs', 'has_no_coles_barcode', 
                        'normalized_name_brand_size_variations', 'sizes', 'company_skus'
                    ]
                    Product.objects.bulk_update(list(self.products_to_update), update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with new information.")

                # Stage 5: Update existing brands
                if self.brands_to_update:
                    brand_update_fields = ['name_variations', 'normalized_name_variations']
                    ProductBrand.objects.bulk_update(list(self.brands_to_update), brand_update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.brands_to_update)} brands with new variation info.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return stale_price_ids
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return None