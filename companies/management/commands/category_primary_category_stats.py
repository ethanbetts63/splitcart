from django.core.management.base import BaseCommand
from django.db.models import Count
from companies.models import PrimaryCategory, Category

class Command(BaseCommand):
    help = 'Reports on the number of Category objects attached to each PrimaryCategory and unassigned categories.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Primary Category Assignment Statistics ---'))

        # 1. Report for each PrimaryCategory
        primary_categories = PrimaryCategory.objects.annotate(
            category_count=Count('categories')
        ).order_by('name')

        self.stdout.write("\nCategories attached per Primary Category:")
        if primary_categories.exists():
            for primary_category in primary_categories:
                self.stdout.write(f"- '{primary_category.name}': {primary_category.category_count} categories")
        else:
            self.stdout.write("  No Primary Categories found.")

        # 2. Report for categories not attached to any PrimaryCategory
        unassigned_categories_count = Category.objects.filter(primary_category__isnull=True).count()

        self.stdout.write("\nCategories not attached to any Primary Category:")
        self.stdout.write(f"- {unassigned_categories_count} categories")
        
        self.stdout.write(self.style.SUCCESS('\n--- Statistics Complete ---'))
