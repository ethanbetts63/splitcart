from django.db import transaction, utils as db_utils
from datetime import datetime
import re
from products.models import Product, Price, ProductBrand
from companies.models import Store 
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

    def _log_problematic_item(self, item_type: str, item_data: dict, error: Exception):
        """Helper method to log details of a problematic item."""
        self.command.stderr.write(self.command.style.ERROR(f"  - Found problematic {item_type}:"))
        for key, value in item_data.items():
            # For product objects, show their string representation
            if isinstance(value, (Product, Store, ProductBrand)):
                value = str(value)
            self.command.stderr.write(self.command.style.ERROR(f"    - {key}: {value}"))
        self.command.stderr.write(self.command.style.ERROR(f"  - Reason: {error}"))

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

                    newly_created_products_with_ids = Product.objects.filter(
                        normalized_name_brand_size__in=new_products_map_by_norm_string.keys()
                    ).in_bulk(field_name='normalized_name_brand_size')

                    for norm_string, product_instance_with_id in newly_created_products_with_ids.items():
                        _, product_details, metadata = new_products_map_by_norm_string[norm_string]
                        self.add_price(product_instance_with_id, store, product_details, metadata)

                    for norm_string, p in newly_created_products_with_ids.items():
                        product_cache[norm_string] = p

                # Stage 2: Upsert Price objects
                stale_price_ids = []
                if self.prices_to_upsert:
                    self.command.stdout.write(f"  - Processing {len(self.prices_to_upsert)} Price objects...")

                    product_id_to_price_id_map = {p['product_id']: p['id'] for p in initial_price_cache}
                    existing_hashes_map = {p['price_hash']: p['id'] for p in initial_price_cache if p['price_hash']}
                    
                    prices_to_create = []
                    prices_to_update = []
                    seen_hashes = set()
                    
                    # Proactive deduplication for the "Duplicate Entry" issue
                    seen_product_store_pairs = set()
                    deduplicated_prices_to_upsert = []
                    for price_data in self.prices_to_upsert:
                        # Product might be new and not have an ID yet if it wasn't created in this UoW
                        if not price_data['product'].id:
                            continue
                        pair = (price_data['product'].id, price_data['store'].id)
                        if pair not in seen_product_store_pairs:
                            deduplicated_prices_to_upsert.append(price_data)
                            seen_product_store_pairs.add(pair)
                    self.prices_to_upsert = deduplicated_prices_to_upsert

                    total_prices = len(self.prices_to_upsert)
                    for i, price_data in enumerate(self.prices_to_upsert):
                        if (i + 1) % 500 == 0 or (i + 1) == total_prices:
                            self.command.stdout.write(f'\r    - Comparing prices: {i + 1}/{total_prices}', ending='')
                        
                        incoming_hash = price_data.get('price_hash')
                        if not incoming_hash: continue
                        seen_hashes.add(incoming_hash)

                        if incoming_hash in existing_hashes_map: continue

                        product_id = price_data['product'].id
                        if product_id in product_id_to_price_id_map:
                            price_id = product_id_to_price_id_map[product_id]
                            price_obj = Price(id=price_id, **price_data)
                            prices_to_update.append(price_obj)
                        else:
                            prices_to_create.append(Price(**price_data))
                    self.command.stdout.write('')

                    if prices_to_create:
                        Price.objects.bulk_create(prices_to_create, batch_size=500)
                        self.command.stdout.write(f"  - Created {len(prices_to_create)} new Price objects.")

                    if prices_to_update:
                        update_fields = list(self.prices_to_upsert[0].keys())
                        update_fields.remove('product')
                        update_fields.remove('store')
                        Price.objects.bulk_update(prices_to_update, update_fields, batch_size=500)
                        self.command.stdout.write(f"  - Updated {len(prices_to_update)} existing Price objects.")

                    stale_hashes = set(existing_hashes_map.keys()) - seen_hashes
                    stale_price_ids = [existing_hashes_map[h] for h in stale_hashes]

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store.company)

                # Stage 4: Update existing products
                if self.products_to_update:
                    update_fields = [
                        'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode', 
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

        except (db_utils.IntegrityError, db_utils.DataError) as e:
            self.command.stderr.write(self.command.style.ERROR(f'\nAn error occurred during commit: {e}'))
            self.command.stderr.write(self.command.style.ERROR('Performing forensic analysis to identify the problematic item...'))

            error_str = str(e)
            found_culprit = False

            if isinstance(e, db_utils.IntegrityError) and "Duplicate entry" in error_str:
                match = re.search(r"Duplicate entry '(.+?)' for key", error_str)
                if match:
                    duplicate_values = match.group(1)
                    if 'products_price' in error_str:
                        try:
                            prod_id, store_id_val = duplicate_values.split('-')
                            for price_data in self.prices_to_upsert:
                                if str(price_data['product'].id) == prod_id and str(price_data['store'].id) == store_id_val:
                                    self._log_problematic_item("Price", price_data, e)
                                    found_culprit = True
                                    break
                        except (ValueError, KeyError):
                            pass # Could not parse values or item not found

            elif isinstance(e, db_utils.DataError) and "Out of range value" in error_str:
                # This is a best-effort guess. The row number is not reliably tied to a specific list.
                # We can't know which bulk operation failed from this single except block.
                self.command.stderr.write(self.command.style.WARNING("  - Could not definitively identify the item with the 'Out of range' value."))
                self.command.stderr.write(self.command.style.WARNING("  - This error requires breaking the transaction into smaller parts to isolate."))

            if not found_culprit:
                self.command.stderr.write(self.command.style.WARNING("  - Forensic analysis could not pinpoint the exact item."))
            
            return None
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An unexpected error occurred during commit: {e}'))
            import traceback
            self.command.stderr.write(traceback.format_exc())
            return None
