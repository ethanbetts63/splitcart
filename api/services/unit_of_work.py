from django.db import transaction
from products.models import Product, Price

class UnitOfWork:
    """
    Manages database transactions and batch operations for the update process.
    """
    def __init__(self, command):
        self.command = command
        self.products_to_create = []
        self.prices_to_create = []
        self.products_to_update = []

    def add_new_product(self, product_instance):
        self.products_to_create.append(product_instance)

    def add_new_price(self, price_instance):
        self.prices_to_create.append(price_instance)

    def add_for_update(self, product_instance):
        # Avoid adding the same product multiple times
        if product_instance not in self.products_to_update:
            self.products_to_update.append(product_instance)

    def report_pre_commit_summary(self):
        self.command.stdout.write("--- Pre-Commit Summary ---")
        self.command.stdout.write(f"  - Found {len(self.products_to_create)} potential new products.")
        self.command.stdout.write(f"  - Found {len(self.prices_to_create)} new price records.")
        self.command.stdout.write(f"  - Found {len(self.products_to_update)} products with name variations to update.")

    def commit(self):
        """
        Executes the bulk create and update operations within a single atomic transaction.
        """
        self.report_pre_commit_summary()
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Create Products
                if self.products_to_create:
                    Product.objects.bulk_create(self.products_to_create, batch_size=500)
                    self.command.stdout.write(f"  - Created {len(self.products_to_create)} new products.")

                # Create Prices
                if self.prices_to_create:
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500)
                    self.command.stdout.write(f"  - Created {len(self.prices_to_create)} new price records.")

                # Update Products
                if self.products_to_update:
                    Product.objects.bulk_update(self.products_to_update, ['name_variations'], batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with name variations.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False