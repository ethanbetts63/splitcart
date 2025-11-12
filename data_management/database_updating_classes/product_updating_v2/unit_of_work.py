from django.db import transaction
from products.models import Product

class UnitOfWork:
    """
    Collects all proposed database changes for a single file and
    executes them in a single, atomic transaction.
    """
    def __init__(self, command):
        self.command = command
        self.products_to_create = []
        self.products_to_update = []
        # Price-related lists will be added later
        # self.prices_to_create = []
        # self.prices_to_update = []
        # self.prices_to_delete = []

    def add_products_for_creation(self, products):
        """Receives a list of Product instances to be created."""
        self.products_to_create.extend(products)

    def add_products_for_update(self, products):
        """Receives a list of Product instances to be updated."""
        self.products_to_update.extend(products)

    def commit(self):
        """
        Executes the database operations in a single transaction.
        Currently only handles bulk creation of products.
        """
        if not self.products_to_create and not self.products_to_update:
            self.command.stdout.write("  - Unit of Work: No database changes to commit.")
            return

        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                if self.products_to_create:
                    self.command.stdout.write(f"  - Creating {len(self.products_to_create)} new products.")
                    Product.objects.bulk_create(self.products_to_create, batch_size=500)
                
                # Stage 2: Update existing products
                if self.products_to_update:
                    self.command.stdout.write(f"  - Updating {len(self.products_to_update)} existing products.")
                    # Define update_fields based on what ProductEnricher will modify
                    update_fields = [
                        'name', 'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                        'normalized_name_brand_size_variations', 'sizes', 'company_skus',
                        'brand', # Assuming brand can be updated
                    ]
                    Product.objects.bulk_update(self.products_to_update, update_fields, batch_size=500)

            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An unexpected error occurred during commit: {e}'))
            # Rollback is automatic with transaction.atomic
            raise
