from django.core.management.base import BaseCommand
from companies.models import Category

class Command(BaseCommand):
    help = 'Checks which categories have the is_popular flag set to True.'

    def handle(self, *args, **options):
        popular_categories = Category.objects.filter(is_popular=True).order_by('name')

        if popular_categories.exists():
            self.stdout.write(self.style.SUCCESS('The following categories have is_popular=True:'))
            for category in popular_categories:
                self.stdout.write(f'- {category.name}')
        else:
            self.stdout.write(self.style.WARNING('No categories have the is_popular flag set to True.'))
