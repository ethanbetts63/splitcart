from django.core.management.base import BaseCommand
from companies.models import Category, Company
from django.db.models import Count

class Command(BaseCommand):
    help = 'Inspects the state of categories in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            help='The name of the company to inspect.'
        )

    def handle(self, *args, **options):
        company_name = options['company_name']
        target_company = None

        self.stdout.write(self.style.SUCCESS("--- Inspecting Category Data ---"))

        if company_name:
            try:
                target_company = Company.objects.get(name__iexact=company_name)
                self.stdout.write(self.style.SUCCESS(f"Filtering for company: {target_company.name}\n"))
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Company '{company_name}' not found."))
                return

        # Base querysets
        category_qs = Category.objects.all()
        company_qs = Company.objects.all()

        if target_company:
            category_qs = category_qs.filter(company=target_company)
            company_qs = company_qs.filter(id=target_company.id)

        total_categories = category_qs.count()

        if not target_company:
            total_companies = company_qs.count()
            self.stdout.write(f"\n- Total Companies: {total_companies}")
        
        self.stdout.write(f"- Total Categories: {total_categories}")

        if total_categories == 0:
            self.stdout.write(self.style.WARNING("\nNo categories found for the given scope."))
            return

        if not target_company:
            self.stdout.write(self.style.SUCCESS("\n--- Categories per Company ---"))
            company_category_counts = company_qs.annotate(num_cats=Count('categories')).order_by('-num_cats')
            for company in company_category_counts:
                self.stdout.write(f"- {company.name}: {company.num_cats} categories")

        self.stdout.write(self.style.SUCCESS("\n--- Sample Categories (first 20) ---"))
        sample_categories = category_qs.prefetch_related('parents')[:20]
        
        for i, category in enumerate(sample_categories):
            parent_names = ", ".join([p.name for p in category.parents.all()])
            if not parent_names:
                parent_names = "None"
            
            self.stdout.write(
                f"{i+1}. Category: '{category.name}' (Company: {category.company.name})\n"
                f"   - Parents: {parent_names}\n"
                f"--------------------"
            )
