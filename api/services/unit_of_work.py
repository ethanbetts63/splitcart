from django.db import transaction
from products.models import Product, Price
from .category_manager import CategoryManager

class UnitOfWork:
    """
    Manages database transactions and batch operations for the update process.
    """
    def __init__(self, command):
        self.command = command
        self.products_to_create = []
        self.prices_to_create = []
        self.products_to_update = []
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance):
        self.products_to_create.append(product_instance)

    def add_new_price(self, price_instance):
        self.prices_to_create.append(price_instance)

    def add_for_update(self, product_instance):
        if product_instance not in self.products_to_update:
            self.products_to_update.append(product_instance)

    def report_pre_commit_summary(self):
        self.command.stdout.write("--- Pre-Commit Summary ---")
        self.command.stdout.write(f"  - Found {len(self.products_to_create)} potential new products.")
        self.command.stdout.write(f"  - Found {len(self.prices_to_create)} new price records.")
        self.command.stdout.write(f"  - Found {len(self.products_to_update)} products with name variations to update.")

    def commit(self, consolidated_data, product_cache, resolver):
        """
        Executes the bulk create and update operations within a single atomic transaction.
        """
        self.report_pre_commit_summary()
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                if self.products_to_create:
                    # De-duplicate the list of new products before creating them
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

                    self.command.stdout.write(f"  - Creating {len(unique_new_products)} truly unique new products.")
                    if unique_new_products:
                        Product.objects.bulk_create(unique_new_products, batch_size=500)
                        # After creating, we need to refresh the product_cache with the new products
                        for p in unique_new_products:
                            product_cache[p.normalized_name_brand_size] = p

                # Now that all products exist, process categories
                self.category_manager.process_categories(consolidated_data, product_cache)

                if self.prices_to_create:
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500)
                    self.command.stdout.write(f"  - Created {len(self.prices_to_create)} new price records.")

                if self.products_to_update:
                    Product.objects.bulk_update(self.products_to_update, ['name_variations'], batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with name variations.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False