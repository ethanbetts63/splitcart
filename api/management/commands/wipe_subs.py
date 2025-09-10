from django.core.management.base import BaseCommand
from products.models import ProductSubstitution

class Command(BaseCommand):
    help = 'Deletes all product substitutions from the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- Deleting all product substitutions ---'))
        count, _ = ProductSubstitution.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} product substitutions.'))
