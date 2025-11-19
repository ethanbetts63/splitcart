from django.core.management.base import BaseCommand
from django.db.models import F, Subquery, OuterRef
from itertools import combinations
from companies.models import PrimaryCategory, Company
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Compares product prices between company pairs for primary categories and updates the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting price comparison update..."))

        categories = PrimaryCategory.objects.all().order_by('name')
        company_names = ["Coles", "Woolworths", "IGA", "Aldi"]
        companies_to_compare = list(Company.objects.filter(name__in=company_names))
        
        if len(companies_to_compare) < 2:
            self.stdout.write(self.style.ERROR("Need at least two of the major companies to compare."))
            return

        total_categories = categories.count()
        for i, category in enumerate(categories):
            self.stdout.write(self.style.HTTP_INFO(f"\n--- Analyzing Category ({i+1}/{total_categories}): {category.name} ---"))
            category.price_comparison_data = {"comparisons": []}

            for company_a, company_b in combinations(companies_to_compare, 2):
                self.stdout.write(f"  Comparing {company_a.name} vs {company_b.name} for {category.name}...")

                product_ids_a = set(Product.objects.filter(
                    category__primary_category=category,
                    prices__store__company=company_a
                ).values_list('id', flat=True))
                
                product_ids_b = set(Product.objects.filter(
                    category__primary_category=category,
                    prices__store__company=company_b
                ).values_list('id', flat=True))

                overlapping_product_ids = list(product_ids_a.intersection(product_ids_b))
                
                if len(overlapping_product_ids) < 5:
                    self.stdout.write(f"    Skipping: Only {len(overlapping_product_ids)} common products initially (less than 5 required).")
                    continue
                
                overlapping_products_qs = Product.objects.filter(id__in=overlapping_product_ids)
                
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

                products_with_prices = overlapping_products_qs.annotate(
                    price_a=price_a_subquery,
                    price_b=price_b_subquery
                ).filter(price_a__isnull=False, price_b__isnull=False)

                overlap_count = products_with_prices.count()

                if overlap_count < 5:
                    self.stdout.write(f"    Skipping: Only {overlap_count} overlapping products with valid prices (less than 5 required).")
                    continue
                
                cheaper_at_a = products_with_prices.filter(price_a__lt=F('price_b')).count()
                cheaper_at_b = products_with_prices.filter(price_b__lt=F('price_a')).count()
                same_price = products_with_prices.filter(price_a=F('price_b')).count()

                cheaper_at_a_percent = round((cheaper_at_a / overlap_count) * 100) if overlap_count > 0 else 0
                cheaper_at_b_percent = round((cheaper_at_b / overlap_count) * 100) if overlap_count > 0 else 0
                same_price_percent = round((same_price / overlap_count) * 100) if overlap_count > 0 else 0

                comparison_data = {
                    "company_a_id": company_a.id,
                    "company_a_name": company_a.name,
                    "company_b_id": company_b.id,
                    "company_b_name": company_b.name,
                    "overlap_count": overlap_count,
                    "cheaper_at_a_percentage": cheaper_at_a_percent,
                    "cheaper_at_b_percentage": cheaper_at_b_percent,
                    "same_price_percentage": same_price_percent,
                }
                category.price_comparison_data["comparisons"].append(comparison_data)
                self.stdout.write(f"    Comparison added: {company_a.name} vs {company_b.name} (Overlap: {overlap_count})")


            category.save()
            self.stdout.write(self.style.SUCCESS(f"  Category '{category.name}' comparison data saved."))


        self.stdout.write(self.style.SUCCESS("\n--- Price comparison data updated successfully for all categories. ---"))
        self.stdout.write("\n--- Stored Comparison Data Summary ---")
        for category in PrimaryCategory.objects.filter(price_comparison_data__comparisons__isnull=False).distinct():
             self.stdout.write(self.style.WARNING(f"\nCategory: {category.name}"))
             if category.price_comparison_data and category.price_comparison_data.get("comparisons"):
                 for comp in category.price_comparison_data["comparisons"]:
                    self.stdout.write(f"  - {comp['company_a_name']} ({comp['cheaper_at_a_percentage']}%) vs {comp['company_b_name']} ({comp['cheaper_at_b_percentage']}%): Same ({comp['same_price_percentage']}%) | Overlap: {comp['overlap_count']}")
             else:
                 self.stdout.write("  No comparison data for this category.")

