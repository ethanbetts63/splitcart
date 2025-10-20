from django.core.management.base import BaseCommand
from users.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Deletes user accounts. By default, deletes non-superuser accounts. Use --all to delete all accounts, including superusers.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all user accounts, including superusers.',
        )

    def handle(self, *args, **options):
        delete_all = options['all']

        if delete_all:
            self.stdout.write(self.style.WARNING('Starting the process to delete ALL user accounts (including superusers)...'))
            users_to_delete = User.objects.all()
        else:
            self.stdout.write(self.style.WARNING('Starting the process to delete non-superuser accounts...'))
            users_to_delete = User.objects.filter(is_superuser=False)

        try:
            with transaction.atomic():
                count = users_to_delete.count()

                if count == 0:
                    if delete_all:
                        self.stdout.write(self.style.SUCCESS('No user accounts found to delete.'))
                    else:
                        self.stdout.write(self.style.SUCCESS('No non-superuser accounts found to delete.'))
                    return

                # Delete the users
                users_to_delete.delete()

                if delete_all:
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} user account(s) (including superusers).'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} non-superuser account(s).'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.ERROR('Operation failed. No users were deleted.'))
