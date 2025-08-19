from django.core.management.base import BaseCommand
from companies.models import Company, Category
from django.db.models import Count

class Command(BaseCommand):
    help = 'Finds and lists the IDs of duplicate categories.'

    def handle(self, *args, **options):
        duplicates = Category.objects.values('name', 'company__name').annotate(name_count=Count('id')).filter(name_count__gt=1)
        
        if duplicates.exists():
            self.stdout.write(self.style.WARNING("Found duplicate categories. Here are their IDs:"))
            for duplicate in duplicates:
                self.stdout.write(self.style.SUCCESS(f"--- {duplicate['company__name']} - {duplicate['name']} ---"))
                categories = Category.objects.filter(name=duplicate['name'], company__name=duplicate['company__name'])
                for category in categories:
                    self.stdout.write(f"  - ID: {category.id}, Name: {category.name}, Slug: {category.slug}")
        else:
            self.stdout.write(self.style.SUCCESS("No duplicate categories found."))
