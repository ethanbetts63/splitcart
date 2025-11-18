from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from companies.models import PrimaryCategory, Company
from products.models import Product

class Command(BaseCommand):
    help = 'Displays statistics for each primary category regarding company distribution and product availability.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Calculating primary category statistics...'))

        company_names = ["Coles", "Woolworths", "IGA", "Aldi"]
        num_major_companies = len(company_names)

        # Annotate each product with the number of major companies that sell it
        products_with_company_count = Product.objects.annotate(
            num_companies=Count(
                'prices__store__company',
                filter=Q(prices__store__company__name__in=company_names),
                distinct=True
            )
        )

        primary_categories = PrimaryCategory.objects.all().order_by('name')

        for category in primary_categories:
            # Filter annotated products for the current category
            annotated_products_in_category = products_with_company_count.filter(category__primary_category=category)
            
            # 1. Number of companies (any company) with at least one product in this category
            num_companies_with_products = Company.objects.filter(
                stores__prices__product__category__primary_category=category
            ).distinct().count()

            # 2. Number of products in the category available at all MAJOR companies
            num_products_in_all = annotated_products_in_category.filter(num_companies=num_major_companies).count()

            self.stdout.write(f"\n--- {category.name} ---")
            self.stdout.write(f"  Companies with products: {num_companies_with_products}")
            self.stdout.write(f"  Products available in all {num_major_companies} major companies: {num_products_in_all}")

        self.stdout.write(self.style.SUCCESS('\nDone.'))
