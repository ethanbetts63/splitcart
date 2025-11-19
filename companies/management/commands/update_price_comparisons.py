from django.core.management.base import BaseCommand
from django.db.models import Min, F
from itertools import combinations
from collections import defaultdict
from companies.models import PrimaryCategory, Company
from products.models import Price

class Command(BaseCommand):
    help = 'Efficiently compares product prices and updates the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting price comparison update (high-efficiency)..."))

        company_names = ["Coles", "Woolworths", "IGA", "Aldi"]
        companies = {c.id: c for c in Company.objects.filter(name__in=company_names)}
        
        if len(companies) < 2:
            self.stdout.write(self.style.ERROR("Need at least two major companies to compare."))
            return

        all_categories = list(PrimaryCategory.objects.all().order_by('name'))
        categories_to_update = []
        total_categories = len(all_categories)

        for i, category in enumerate(all_categories):
            self.stdout.write(self.style.HTTP_INFO(f"\n--- Analyzing Category ({i+1}/{total_categories}): {category.name} ---"))
            
            # 1. Bulk fetch all prices for the current primary category
            prices_qs = Price.objects.filter(
                product__category__primary_category=category,
                store__company_id__in=companies.keys()
            ).values('product_id', 'store__company_id').annotate(min_price=Min('price'))

            # 2. Process data in-memory
            product_prices_by_company = defaultdict(dict)
            for price_data in prices_qs:
                product_prices_by_company[price_data['product_id']][price_data['store__company_id']] = price_data['min_price']

            category.price_comparison_data = {"comparisons": []}
            
            # Iterate through company pairs to perform in-memory comparison
            for comp_a_id, comp_b_id in combinations(companies.keys(), 2):
                company_a = companies[comp_a_id]
                company_b = companies[comp_b_id]
                self.stdout.write(f"  Comparing {company_a.name} vs {company_b.name}...")

                cheaper_at_a, cheaper_at_b, same_price = 0, 0, 0
                
                # Find overlapping products in-memory
                overlapping_products = [
                    p for p, prices in product_prices_by_company.items()
                    if comp_a_id in prices and comp_b_id in prices
                ]
                
                overlap_count = len(overlapping_products)

                if overlap_count < 5:
                    self.stdout.write(f"    Skipping: Only {overlap_count} overlapping products (less than 5 required).")
                    continue

                for product_id in overlapping_products:
                    price_a = product_prices_by_company[product_id][comp_a_id]
                    price_b = product_prices_by_company[product_id][comp_b_id]
                    if price_a < price_b:
                        cheaper_at_a += 1
                    elif price_b < price_a:
                        cheaper_at_b += 1
                    else:
                        same_price += 1

                cheaper_at_a_percent = round((cheaper_at_a / overlap_count) * 100)
                cheaper_at_b_percent = round((cheaper_at_b / overlap_count) * 100)
                same_price_percent = round((same_price / overlap_count) * 100)

                category.price_comparison_data["comparisons"].append({
                    "company_a_id": comp_a_id, "company_a_name": company_a.name,
                    "company_b_id": comp_b_id, "company_b_name": company_b.name,
                    "overlap_count": overlap_count,
                    "cheaper_at_a_percentage": cheaper_at_a_percent,
                    "cheaper_at_b_percentage": cheaper_at_b_percent,
                    "same_price_percentage": same_price_percent,
                })
                self.stdout.write(f"    Comparison added (Overlap: {overlap_count})")
            
            categories_to_update.append(category)

        # 3. Bulk update
        if categories_to_update:
            self.stdout.write(self.style.SUCCESS("\nSaving all updated data to the database..."))
            PrimaryCategory.objects.bulk_update(categories_to_update, ['price_comparison_data'])
            self.stdout.write(self.style.SUCCESS("Database update complete."))
        else:
            self.stdout.write(self.style.WARNING("No categories were updated."))

        self.stdout.write("\n--- Stored Comparison Data Summary ---")
        for category in categories_to_update:
            self.stdout.write(self.style.WARNING(f"\nCategory: {category.name}"))
            if category.price_comparison_data and category.price_comparison_data.get("comparisons"):
                for comp in category.price_comparison_data["comparisons"]:
                   self.stdout.write(f"  - {comp['company_a_name']} ({comp['cheaper_at_a_percentage']}%) vs {comp['company_b_name']} ({comp['cheaper_at_b_percentage']}%): Same ({comp['same_price_percentage']}%) | Overlap: {comp['overlap_count']}")
            else:
                self.stdout.write("  No comparison data for this category.")

