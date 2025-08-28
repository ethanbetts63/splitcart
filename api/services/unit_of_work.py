from django.db import transaction
from products.models import Product, Price
from .category_manager import CategoryManager

class UnitOfWork:
    def __init__(self, command):
        self.command = command
        self.products_to_create = []
        self.prices_to_create = []
        self.products_to_update = []
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance):
        self.products_to_create.append(product_instance)

    def add_price(self, product, store, product_details):
        price_value = product_details.get('price_current')
        # If price is None or 0, skip creating the record.
        if not price_value:
            return

        self.prices_to_create.append(
            Price(
                product=product, 
                store=store, 
                price=price_value, 
                store_product_id=product_details.get('product_id_store')
            )
        )

    def add_for_update(self, product_instance):
        if product_instance not in self.products_to_update:
            self.products_to_update.append(product_instance)

    def _deduplicate_new_products(self, resolver):
        unique_new_products = []
        seen_barcodes = set(resolver.barcode_cache.keys())
        seen_normalized_strings = set(resolver.normalized_string_cache.keys())

        for product in self.products_to_create:
            if product.barcode and product.barcode in seen_barcodes:
                continue
            if product.normalized_name_brand_size and product.normalized_name_brand_size in seen_normalized_strings:
                continue
            
            unique_new_products.append(product)
            if product.barcode:
                seen_barcodes.add(product.barcode)
            if product.normalized_name_brand_size:
                seen_normalized_strings.add(product.normalized_name_brand_size)
        return unique_new_products

    def commit(self, consolidated_data, product_cache, resolver):
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                unique_new_products = self._deduplicate_new_products(resolver)
                if unique_new_products:
                    self.command.stdout.write(f"  - Creating {len(unique_new_products)} truly unique new products.")
                    Product.objects.bulk_create(unique_new_products, batch_size=500)
                    # Refresh the product_cache with the newly created products
                    for p in unique_new_products:
                        product_cache[p.normalized_name_brand_size] = p

                # Stage 2: Create prices
                if self.prices_to_create:
                    self.command.stdout.write(f"  - Creating {len(self.prices_to_create)} new price records.")
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500)

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache)

                # Stage 4: Update existing products
                if self.products_to_update:
                    Product.objects.bulk_update(self.products_to_update, ['name_variations'], batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with name variations.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False