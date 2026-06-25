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

        major_companies = list(Company.objects.filter(name__in=company_names))
        company_ids = [c.id for c in major_companies]

        primary_categories = PrimaryCategory.objects.all().order_by('name')

        for category in primary_categories:
            slug = category.slug

            # Products in this primary category (via primary_category_slugs JSON field)
            products_in_cat = Product.objects.filter(primary_category_slugs__contains=[slug])

            # Companies with at least one product in this category
            num_companies_with_products = Company.objects.filter(
                stores__prices__product__primary_category_slugs__contains=[slug]
            ).distinct().count()

            # Products in the category sold by all major companies
            products_in_all = products_in_cat.annotate(
                num_major_companies=Count(
                    'prices__store__company',
                    filter=Q(prices__store__company__name__in=company_names),
                    distinct=True,
                )
            ).filter(num_major_companies=num_major_companies).count()

            self.stdout.write(f"\n--- {category.name} ---")
            self.stdout.write(f"  Companies with products: {num_companies_with_products}")
            self.stdout.write(f"  Products available in all {num_major_companies} major companies: {products_in_all}")

        self.stdout.write(self.style.SUCCESS('\nDone.'))
