from django.core.management.base import BaseCommand
from django.db.models import Q, F, Subquery, OuterRef
from itertools import combinations
from companies.models import Company
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Performs an overall comparison of product prices between pairs of companies.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Overall Company Price Comparison ---'))

        company_names = ["Coles", "Woolworths", "IGA", "Aldi"]
        companies_to_compare = list(Company.objects.filter(name__in=company_names))
        
        if len(companies_to_compare) < 2:
            self.stdout.write(self.style.ERROR("Need at least two of the major companies in the database to compare."))
            return

        for company_a, company_b in combinations(companies_to_compare, 2):
            self.stdout.write(f"\nComparing {company_a.name} vs {company_b.name}...")

            # Get IDs of all products for each company
            product_ids_a = set(Product.objects.filter(
                prices__store__company=company_a
            ).values_list('id', flat=True))
            
            product_ids_b = set(Product.objects.filter(
                prices__store__company=company_b
            ).values_list('id', flat=True))

            # Find the intersection of product IDs
            overlapping_product_ids = list(product_ids_a.intersection(product_ids_b))

            if not overlapping_product_ids:
                self.stdout.write("    No overlapping products found.")
                continue
            
            # Create a queryset from the overlapping IDs
            overlapping_products_qs = Product.objects.filter(id__in=overlapping_product_ids)
            
            # Create subqueries to fetch the minimum price for each product at each company
            price_a_subquery = Subquery(
                Price.objects.filter(
                    product=OuterRef('pk'),
                    store__company=company_a
                ).order_by('price').values('price')[:1]
            )
            price_b_subquery = Subquery(
                Price.objects.filter(
                    product=OuterRef('pk'),
                    store__company=company_b
                ).order_by('price').values('price')[:1]
            )

            # Annotate the overlapping products with their prices from each company
            products_with_prices = overlapping_products_qs.annotate(
                price_a=price_a_subquery,
                price_b=price_b_subquery
            ).filter(price_a__isnull=False, price_b__isnull=False)

            overlap_count = products_with_prices.count()

            if overlap_count == 0:
                self.stdout.write("    No overlapping products with valid prices found for comparison.")
                continue
            
            # Perform the price comparison using the annotated fields
            cheaper_at_a = products_with_prices.filter(price_a__lt=F('price_b')).count()
            cheaper_at_b = products_with_prices.filter(price_b__lt=F('price_a')).count()
            same_price = products_with_prices.filter(price_a=F('price_b')).count()

            # Calculate percentages
            cheaper_at_a_percent = (cheaper_at_a / overlap_count) * 100 if overlap_count > 0 else 0
            cheaper_at_b_percent = (cheaper_at_b / overlap_count) * 100 if overlap_count > 0 else 0
            same_price_percent = (same_price / overlap_count) * 100 if overlap_count > 0 else 0

            self.stdout.write(f"  Product Overlap: {overlap_count} products")
            self.stdout.write(f"    - Cheaper at {company_a.name}: {cheaper_at_a_percent:.2f}% ({cheaper_at_a} products)")
            self.stdout.write(f"    - Cheaper at {company_b.name}: {cheaper_at_b_percent:.2f}% ({cheaper_at_b} products)")
            self.stdout.write(f"    - Same price: {same_price_percent:.2f}% ({same_price} products)")

        self.stdout.write(self.style.SUCCESS('\nComparison complete.'))
