from django.db.models import Count, Avg
from itertools import combinations
from collections import defaultdict
from companies.models import PrimaryCategory, Company
from products.models import Price

class PriceComparisonsGenerator:
    def __init__(self, command):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style

    def run(self):
        self.stdout.write(self.style.SUCCESS("Starting price comparison update..."))

        company_names = ["Coles", "Woolworths", "IGA", "Aldi"]
        companies = {c.id: c for c in Company.objects.filter(name__in=company_names)}
        
        if len(companies) < 2:
            self.stdout.write(self.style.ERROR("Need at least two major companies to compare."))
            return

        self.stdout.write(self.style.HTTP_INFO("Step 1/4: Identifying products sold by multiple companies..."))
        relevant_product_ids = Price.objects.filter(
            store__company_id__in=companies.keys()
        ).values('product_id').annotate(
            company_count=Count('store__company', distinct=True)
        ).filter(company_count__gte=2).values_list('product_id', flat=True)
        self.stdout.write(f"Found {len(relevant_product_ids)} relevant products.")

        self.stdout.write(self.style.HTTP_INFO("Step 2/4: Building slim price cache with average prices..."))
        price_data_qs = Price.objects.filter(
            product_id__in=list(relevant_product_ids),
            store__company_id__in=companies.keys()
        ).values(
            'product__category__primary_category_id',
            'product_id',
            'store__company_id'
        ).annotate(avg_price=Avg('price'))

        self.stdout.write(self.style.HTTP_INFO("Step 3/4: Structuring cached data for in-memory processing..."))
        all_prices_by_category = defaultdict(lambda: defaultdict(dict))
        for price_data in price_data_qs:
            cat_id = price_data['product__category__primary_category_id']
            prod_id = price_data['product_id']
            comp_id = price_data['store__company_id']
            price = price_data['avg_price']
            if cat_id:
                all_prices_by_category[cat_id][prod_id][comp_id] = price

        self.stdout.write(self.style.HTTP_INFO("Step 4/4: Performing in-memory comparisons for all categories..."))
        all_categories = list(PrimaryCategory.objects.all().order_by('name'))
        categories_to_update = []
        for category in all_categories:
            category.price_comparison_data = {"comparisons": []}
            product_prices_by_company = all_prices_by_category.get(category.id, {})

            for comp_a_id, comp_b_id in combinations(companies.keys(), 2):
                company_a = companies[comp_a_id]
                company_b = companies[comp_b_id]

                cheaper_at_a, cheaper_at_b, same_price = 0, 0, 0
                
                overlapping_products = [
                    p for p, prices in product_prices_by_company.items()
                    if comp_a_id in prices and comp_b_id in prices
                ]
                
                overlap_count = len(overlapping_products)
                if overlap_count < 5:
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

                category.price_comparison_data["comparisons"].append({
                    "company_a_id": comp_a_id, "company_a_name": company_a.name,
                    "company_b_id": comp_b_id, "company_b_name": company_b.name,
                    "overlap_count": overlap_count,
                    "cheaper_at_a_percentage": round((cheaper_at_a / overlap_count) * 100),
                    "cheaper_at_b_percentage": round((cheaper_at_b / overlap_count) * 100),
                    "same_price_percentage": round((same_price / overlap_count) * 100),
                })
            
            if category.price_comparison_data["comparisons"]:
                categories_to_update.append(category)

        if categories_to_update:
            self.stdout.write(self.style.SUCCESS(f"\nSaving data for {len(categories_to_update)} categories to the database..."))
            PrimaryCategory.objects.bulk_update(categories_to_update, ['price_comparison_data'])
            self.stdout.write(self.style.SUCCESS("Database update complete."))
        else:
            self.stdout.write(self.style.WARNING("No categories had sufficient data to warrant a database update."))

        self.stdout.write("\n--- Stored Comparison Data Summary ---")
        for category in categories_to_update:
            self.stdout.write(self.style.WARNING(f"\nCategory: {category.name}"))
            for comp in category.price_comparison_data["comparisons"]:
               self.stdout.write(f"  - {comp['company_a_name']} vs {comp['company_b_name']}: Overlap {comp['overlap_count']}")
