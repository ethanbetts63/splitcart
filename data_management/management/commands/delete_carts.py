from django.core.management.base import BaseCommand
from users.models import Cart
from django.db import transaction

class Command(BaseCommand):
    help = 'Deletes all carts and their related items.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting the process to delete ALL carts...'))

        try:
            with transaction.atomic():
                carts_to_delete = Cart.objects.all()
                count = carts_to_delete.count()

                if count == 0:
                    self.stdout.write(self.style.SUCCESS('No carts found to delete.'))
                    return

                # Deleting carts will also delete related CartItems and CartSubstitutions due to on_delete=CASCADE
                carts_to_delete.delete()

                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} cart(s) and all related items.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.ERROR('Operation failed. No carts were deleted.'))
