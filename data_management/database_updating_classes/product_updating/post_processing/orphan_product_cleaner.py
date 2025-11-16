from products.models import Product
from django.db import transaction

class OrphanProductCleaner:
    """
    A post-processing utility to find and delete products that have no associated prices.
    """
    def __init__(self, command):
        self.command = command

    def run(self):
        """
        Finds and deletes all Product objects that are not linked to any Price objects.
        """
        self.command.stdout.write("--- Running Orphan Product Cleaner ---")

        try:
            # This is the most efficient way to find all products with no related prices.
            # It translates to a single SQL query with a LEFT JOIN.
            orphans_to_delete = Product.objects.filter(prices__isnull=True)
            
            count = orphans_to_delete.count()

            if count == 0:
                self.command.stdout.write("  - No orphan products found.")
                return

            self.command.stdout.write(self.command.style.WARNING(f"  - Found {count} orphan products to delete."))

            # .delete() on a queryset is a single, efficient bulk operation.
            with transaction.atomic():
                deleted_count, _ = orphans_to_delete.delete()

            self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully deleted {deleted_count} orphan products."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"  - An error occurred during orphan product cleanup: {e}"))
            raise
