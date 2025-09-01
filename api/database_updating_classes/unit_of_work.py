from django.db import transaction
from products.models import Product, Price
from .category_manager import CategoryManager

class UnitOfWork:
    def __init__(self, command):
        self.command = command
        self.new_products_to_process = []
        self.prices_to_create = []
        self.products_to_update = []
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance, product_details):
        """
        Adds a new product instance along with its raw details for later processing.
        """
        self.new_products_to_process.append((product_instance, product_details))

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
                sku=product_details.get('product_id_store')
            )
        )

    def add_for_update(self, product_instance):
        if product_instance not in self.products_to_update:
            self.products_to_update.append(product_instance)

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

    def commit(self, consolidated_data, product_cache, resolver, store_obj):
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
                        self.add_price(product_instance, store_obj, product_details)

                    # Refresh the product_cache with the newly created products
                    for p in new_products:
                        product_cache[p.normalized_name_brand_size] = p

                # Stage 2: Create all prices (for both new and existing products)
                if self.prices_to_create:
                    self.command.stdout.write(f"  - Creating {len(self.prices_to_create)} new price records.")
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500, ignore_conflicts=True)

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store_obj)

                # Stage 4: Update existing products
                if self.products_to_update:
                    update_fields = [
                        'barcode', 'url', 'image_url', 'description', 
                        'country_of_origin', 'ingredients', 'has_no_coles_barcode', 
                        'name_variations', 'normalized_string_variations'
                    ]
                    Product.objects.bulk_update(self.products_to_update, update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with new information.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False