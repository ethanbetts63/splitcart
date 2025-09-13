from django.core.management.base import BaseCommand
from products.models import Product
from companies.models import Category
from django.db.models import Count

class Command(BaseCommand):
    help = 'Creates equivalence links between categories based on products that exist in multiple companies.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Category Equivalence Mapping ---"))

        # Find products that are linked to more than one company.
        # A product is linked to a company via its price's store.
        products_in_multiple_companies = Product.objects.annotate(
            company_count=Count('prices__store__company', distinct=True)
        ).filter(company_count__gt=1)

        self.stdout.write(f"Found {products_in_multiple_companies.count()} products existing in multiple companies.")

        links_created = 0
        for product in products_in_multiple_companies:
            # Get all unique categories associated with this product
            categories = set(product.category.all())
            
            if len(categories) < 2:
                continue

            # For every category in the set, add all other categories as equivalents
            categories_list = list(categories)
            for i in range(len(categories_list)):
                for j in range(i + 1, len(categories_list)):
                    cat_a = categories_list[i]
                    cat_b = categories_list[j]

                    # Check if they are already linked before creating a new link
                    if cat_b not in cat_a.equivalent_categories.all():
                        cat_a.equivalent_categories.add(cat_b)
                        # The relationship is symmetrical, so Django handles the reverse link
                        links_created += 1
                        self.stdout.write(f"Linking '{cat_a.name}' ({cat_a.company.name}) <-> '{cat_b.name}' ({cat_b.company.name})")

        self.stdout.write(self.style.SUCCESS(f"\n--- Mapping Complete ---"))
        self.stdout.write(self.style.SUCCESS(f"Created {links_created} new equivalence links between categories."))
