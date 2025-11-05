from django.db import transaction
from datetime import datetime
from products.models import Product, Price, ProductBrand
from companies.models import StoreGroup
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
        self.groups_to_update = []
        self.groups_to_clear_candidates = []
        self.prices_to_upsert = [] # New list to hold data for Price.objects.update_or_create
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance, product_details, metadata):
        """
        Adds a new product instance along with its raw details for later processing.
        """
        self.new_products_to_process.append((product_instance, product_details, metadata))

    def add_price(self, product, store_group, product_details, metadata):
        scraped_date_str = metadata.get('scraped_date')
        price_value = product_details.get('price_current')

        if not scraped_date_str or not price_value:
            return

        try:
            scraped_date = datetime.strptime(scraped_date_str[:10], '%Y-%m-%d').date()
            
            # Prepare data for Price.objects.update_or_create
            price_data = {
                'product': product,
                'store_group': store_group,
                'scraped_date': scraped_date,
                'price': price_value,
                'was_price': product_details.get('price_was'),
                'unit_price': product_details.get('unit_price'),
                'unit_of_measure': product_details.get('unit_of_measure'),
                'per_unit_price_string': product_details.get('per_unit_price_string'),
                'is_on_special': product_details.get('is_on_special', False),
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
        elif isinstance(instance, StoreGroup):
            if instance not in self.groups_to_update:
                self.groups_to_update.append(instance)

    def add_group_to_clear_candidates(self, group):
        if group not in self.groups_to_clear_candidates:
            self.groups_to_clear_candidates.append(group)

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

    def commit(self, consolidated_data, product_cache, resolver, store_group):
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                unique_new_products_with_details = self._deduplicate_new_products(resolver)
                
                if unique_new_products_with_details:
                    new_products = [p for p, d, m in unique_new_products_with_details]
                    self.command.stdout.write(f"  - Creating {len(new_products)} truly unique new products.")
                    # The product objects in `new_products` will have their PKs populated after this call.
                    Product.objects.bulk_create(new_products, batch_size=500)

                    # Now that products are created and have IDs, add their prices to the upsert list
                    for product_instance, product_details, metadata in unique_new_products_with_details:
                        self.add_price(product_instance, store_group, product_details, metadata)

                    # Refresh the product_cache with the newly created products
                    for p in new_products:
                        product_cache[p.normalized_name_brand_size] = p

                # Stage 2: Upsert Price objects
                if self.prices_to_upsert:
                    self.command.stdout.write(f"  - Upserting {len(self.prices_to_upsert)} Price objects.")
                    for price_data in self.prices_to_upsert:
                        Price.objects.update_or_create(
                            product=price_data.pop('product'),
                            store_group=price_data.pop('store_group'),
                            defaults=price_data
                        )

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store_group.company)

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