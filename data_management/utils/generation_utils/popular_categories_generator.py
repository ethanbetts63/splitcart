from collections import defaultdict
from django.db.models import Count
from companies.models import Category, PopularCategory

class PopularCategoriesGenerator:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS('--- Generating Popular Categories ---'))

        # Clear existing popular categories
        PopularCategory.objects.all().delete()
        self.command.stdout.write(self.command.style.NOTICE('Cleared existing popular categories.'))

        # Annotate each category with its product count
        categories_with_counts = Category.objects.annotate(product_count=Count('products'))

        # Group categories by name to aggregate data
        category_groups = defaultdict(lambda: {'product_count': 0, 'companies': set()})

        for category in categories_with_counts:
            group = category_groups[category.name]
            group['product_count'] += category.product_count
            group['companies'].add(category.company.name)

        # Filter for popular categories
        popular_category_groups = {
            name: data for name, data in category_groups.items()
            if data['product_count'] >= 100 and len(data['companies']) >= 3
        }

        if not popular_category_groups:
            self.command.stdout.write(self.command.style.WARNING('No categories met the criteria to be marked as popular.'))
            return

        self.command.stdout.write(self.command.style.SUCCESS(f'Found {len(popular_category_groups)} popular categories to create.'))

        # Create PopularCategory instances
        for name, data in popular_category_groups.items():
            popular_category, created = PopularCategory.objects.get_or_create(name=name)
            
            # Find all category objects with that name
            categories_to_link = Category.objects.filter(name=name)
            
            # Add them to the ManyToManyField
            popular_category.categories.add(*categories_to_link)
            
            self.command.stdout.write(f'  - Created popular category: {name}')

        self.command.stdout.write(self.command.style.SUCCESS('--- Finished Generating Popular Categories ---'))
