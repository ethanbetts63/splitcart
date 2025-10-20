from django.core.management.base import BaseCommand
from users.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Deletes all user accounts that are not superusers.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting the process to delete non-superuser accounts...'))

        try:
            with transaction.atomic():
                # Select users who are not superusers
                users_to_delete = User.objects.filter(is_superuser=False)
                count = users_to_delete.count()

                if count == 0:
                    self.stdout.write(self.style.SUCCESS('No non-superuser accounts found to delete.'))
                    return

                # Delete the users
                users_to_delete.delete()

                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} non-superuser account(s).'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.ERROR('Operation failed. No users were deleted.'))
