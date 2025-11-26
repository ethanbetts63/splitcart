from django.core.management.base import BaseCommand
from products.models import Bargain

class Command(BaseCommand):
    help = 'Deletes all Bargain objects from the database to prepare for a schema migration.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- Attempting to delete all Bargain objects... ---'))
        try:
            count, _ = Bargain.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} Bargain objects.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.WARNING('This may be because the Bargain model and database table are out of sync.'))
            self.stdout.write(self.style.WARNING('If this command fails, you may need to manually drop the `products_bargain` table from your database before running `migrate`.'))
