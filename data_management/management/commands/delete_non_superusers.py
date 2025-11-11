from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Deletes all non-superuser user instances from the database.'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get all non-superuser users
        non_superusers = User.objects.filter(is_superuser=False)
        
        count = non_superusers.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No non-superuser accounts found to delete.'))
            return

        # Delete them
        non_superusers.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} non-superuser accounts.'))
