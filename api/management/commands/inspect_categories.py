from django.core.management.base import BaseCommand
from companies.models import Category, Company
from django.db.models import Count

class Command(BaseCommand):
    help = 'Inspects the state of categories in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Inspecting Category Data ---"))

        total_companies = Company.objects.count()
        total_categories = Category.objects.count()

        self.stdout.write(f"\n- Total Companies: {total_companies}")
        self.stdout.write(f"- Total Categories: {total_categories}")

        if total_categories == 0:
            self.stdout.write(self.style.WARNING("\nNo categories found in the database."))
            return

        self.stdout.write(self.style.SUCCESS("\n--- Categories per Company ---"))
        company_category_counts = Company.objects.annotate(num_cats=Count('categories')).order_by('-num_cats')
        for company in company_category_counts:
            self.stdout.write(f"- {company.name}: {company.num_cats} categories")

        self.stdout.write(self.style.SUCCESS("\n--- Sample Categories (first 20) ---"))
        sample_categories = Category.objects.all().prefetch_related('parents')[:20]
        
        for i, category in enumerate(sample_categories):
            parent_names = ", ".join([p.name for p in category.parents.all()])
            if not parent_names:
                parent_names = "None"
            
            self.stdout.write(
                f"{i+1}. Category: '{category.name}' (Company: {category.company.name})\n"
                f"   - Parents: {parent_names}\n"
                f"--------------------"
            )
