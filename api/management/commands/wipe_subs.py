from django.core.management.base import BaseCommand
from products.models import ProductSubstitution

class Command(BaseCommand):
    help = 'Deletes product substitutions from the database. Can be filtered by level.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            help='Specify the substitution level to delete (e.g., LVL1, LVL2).'
        )

    def handle(self, *args, **options):
        level = options['level']
        
        queryset = ProductSubstitution.objects.all()
        
        if level:
            self.stdout.write(self.style.WARNING(f'--- Deleting Level {level} product substitutions ---'))
            queryset = queryset.filter(level=level)
        else:
            self.stdout.write(self.style.WARNING('--- Deleting all product substitutions ---'))
            
        count, _ = queryset.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} product substitutions.'))
