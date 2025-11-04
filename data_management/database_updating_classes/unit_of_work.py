from django.db import transaction
from datetime import datetime
from products.models import Product, Price, ProductBrand, PriceRecord
from companies.models import StoreGroup
from django.core.exceptions import ValidationError
from decimal import InvalidOperation
from .category_manager import CategoryManager
from data_management.utils.price_normalizer import PriceNormalizer

class UnitOfWork:
    def __init__(self, command, resolver=None):
        self.command = command
        self.resolver = resolver
        self.new_products_to_process = []
        self.prices_to_create = []
        self.prices_to_update = set()
        self.products_to_update = set()
        self.brands_to_update = set()
        self.groups_to_update = []
        self.groups_to_clear_candidates = []
        self.new_price_records_created = 0
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance, product_details):
        """
        Adds a new product instance along with its raw details for later processing.
        """
        self.new_products_to_process.append((product_instance, product_details))

    def add_price(self, product, store_group, product_details):
        scraped_date_str = product_details.get('scraped_date')
        price_value = product_details.get('price_current')

        if not scraped_date_str or not price_value:
            return

        # Generate the normalized_key for the Price object (product_id-group_id)
        price_data_for_key = {
            'product_id': product.id,
            'group_id': store_group.id,
        }
        normalizer_for_key = PriceNormalizer(price_data=price_data_for_key, company=store_group.company.name)
        normalized_key = normalizer_for_key.get_normalized_key()

        if not normalized_key:
            return

        # Always create a new PriceRecord for the incoming data
        try:
            scraped_date = datetime.strptime(scraped_date_str[:10], '%Y-%m-%d').date()
            price_record = PriceRecord.objects.create(
                product=product,
                scraped_date=scraped_date,
                price=price_value,
                was_price=product_details.get('price_was'),
                unit_price=product_details.get('unit_price'),
                unit_of_measure=product_details.get('unit_of_measure'),
                per_unit_price_string=product_details.get('per_unit_price_string'),
                is_on_special=product_details.get('is_on_special', False)
            )
            self.new_price_records_created += 1
        except (ValidationError, InvalidOperation, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f'\nError creating PriceRecord: {e}'))
            self.command.stderr.write(self.command.style.ERROR(f'Problematic product details: {product_details}'))
            return

        # Now, handle the Price object: update existing or create new
        try:
            existing_price = Price.objects.get(normalized_key=normalized_key)
            # If Price object exists, update it
            existing_price.price_record = price_record
            existing_price.source = 'direct_scrape'
            self.prices_to_update.add(existing_price)
        except Price.DoesNotExist:
            # If Price object does not exist, create a new one
            self.prices_to_create.append(
                Price(
                    price_record=price_record,
                    store_group=store_group,
                    normalized_key=normalized_key,
                    source='direct_scrape'
                )
            )

    def add_for_update(self, instance):
        if isinstance(instance, Product):
            self.products_to_update.add(instance)
        elif isinstance(instance, ProductBrand):
            self.brands_to_update.add(instance)
        elif isinstance(instance, StoreGroup):
            if instance not in self.groups_to_update:
                self.groups_to_update.append(instance)

    def add_group_to_clear_candidates(self, group):
        if group not in self.groups_to_clear_candidates:
            self.groups_to_clear_candidates.append(group)

    def _deduplicate_new_products(self, resolver):
        unique_new_products_with_details = []
        seen_barcodes = set(resolver.barcode_cache.keys())
        seen_normalized_strings = set(resolver.normalized_string_cache.keys())

        for product, details in self.new_products_to_process:
            if product.barcode and product.barcode in seen_barcodes:
                continue
            if product.normalized_name_brand_size and product.normalized_name_brand_size in seen_normalized_strings:
                continue
            
            unique_new_products_with_details.append((product, details))
            if product.barcode:
                seen_barcodes.add(product.barcode)
            if product.normalized_name_brand_size:
                seen_normalized_strings.add(product.normalized_name_brand_size)
        return unique_new_products_with_details

    def commit(self, consolidated_data, product_cache, resolver, store_group):
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                unique_new_products_with_details = self._deduplicate_new_products(resolver)
                
                if unique_new_products_with_details:
                    new_products = [p for p, d in unique_new_products_with_details]
                    self.command.stdout.write(f"  - Creating {len(new_products)} truly unique new products.")
                    # The product objects in `new_products` will have their PKs populated after this call.
                    Product.objects.bulk_create(new_products, batch_size=500)

                    # Now that products are created and have IDs, create their prices
                    for product_instance, product_details in unique_new_products_with_details:
                        self.add_price(product_instance, store_group, product_details)

                    # Refresh the product_cache with the newly created products
                    for p in new_products:
                        product_cache[p.normalized_name_brand_size] = p

                # Stage 2: Create all prices (for both new and existing products)
                if self.prices_to_create:
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500, ignore_conflicts=True)

                # Stage 2.1: Update existing Price objects
                if self.prices_to_update:
                    price_update_fields = ['price_record', 'source']
                    Price.objects.bulk_update(list(self.prices_to_update), price_update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.prices_to_update)} existing Price objects.")

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store_group.company)

                # Stage 4: Update existing products
                if self.products_to_update:
                    update_fields = [
                        'barcode', 'url', 'image_url_pairs', 'has_no_coles_barcode', 
                        'name_variations', 'normalized_name_brand_size_variations', 'sizes', 'company_skus'
                    ]
                    Product.objects.bulk_update(list(self.products_to_update), update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with new information.")

                # Stage 5: Update existing brands
                if self.brands_to_update:
                    brand_update_fields = ['name_variations', 'normalized_name_variations']
                    ProductBrand.objects.bulk_update(list(self.brands_to_update), brand_update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.brands_to_update)} brands with new variation info.")

                # Stage 6: Update existing groups
                if self.groups_to_update:
                    group_update_fields = ['ambassador', 'status', 'is_active']
                    StoreGroup.objects.bulk_update(self.groups_to_update, group_update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.groups_to_update)} store groups.")

                # Stage 7: Clear candidates from groups that have been processed
                if self.groups_to_clear_candidates:
                    for group in self.groups_to_clear_candidates:
                        group.candidates.clear()
                    self.command.stdout.write(f"  - Cleared candidates from {len(self.groups_to_clear_candidates)} groups.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False