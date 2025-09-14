import json
from django.core.management.base import BaseCommand
from itertools import combinations
from companies.models import Category

class Command(BaseCommand):
    help = 'Generates a ranked list of suggested category equivalences based on shared products across all levels.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SQL_FIELD("--- Starting Category Suggestion Generation ---"))

        # 1. Get all categories, not just roots
        self.stdout.write("Fetching all categories...")
        all_categories = Category.objects.all().prefetch_related('products', 'company')

        # 2. Group them by company
        categories_by_company = {}
        for category in all_categories:
            company_name = category.company.name
            if company_name not in categories_by_company:
                categories_by_company[company_name] = []
            categories_by_company[company_name].append(category)

        self.stdout.write(f"Found categories for {len(categories_by_company)} companies.")

        # 3. Pre-calculate product sets for each category to optimize
        self.stdout.write("Pre-calculating product sets for all categories...")
        product_sets = {}
        for category in all_categories:
            product_sets[category.id] = set(p.id for p in category.products.all())

        # 4. Iterate through pairs of companies and calculate Jaccard similarity
        company_names = list(categories_by_company.keys())
        suggestions = []

        for company1_name, company2_name in combinations(company_names, 2):
            self.stdout.write(f"\n--- Comparing {company1_name} and {company2_name} ---")
            cat_list1 = categories_by_company[company1_name]
            cat_list2 = categories_by_company[company2_name]

            for i, cat1 in enumerate(cat_list1):
                self.stdout.write(f"\r  - Processing {company1_name} category {i+1}/{len(cat_list1)}", ending='')
                for cat2 in cat_list2:
                    set1 = product_sets[cat1.id]
                    set2 = product_sets[cat2.id]

                    if not set1 or not set2:
                        continue

                    intersection_size = len(set1.intersection(set2))
                    if intersection_size == 0:
                        continue

                    union_size = len(set1.union(set2))
                    jaccard_similarity = intersection_size / union_size if union_size > 0 else 0

                    # 5. Store suggestion if similarity is above a minimum threshold
                    similarity_threshold = 0.05  # Lower threshold to capture more potential suggestions

                    if jaccard_similarity >= similarity_threshold:
                        suggestions.append({
                            'cat1_id': cat1.id,
                            'cat1_name': cat1.name,
                            'cat1_company': company1_name,
                            'cat2_id': cat2.id,
                            'cat2_name': cat2.name,
                            'cat2_company': company2_name,
                            'score': jaccard_similarity,
                            'shared_products': intersection_size
                        })
            self.stdout.write("\n") # Newline after each company pair comparison

        # 6. Sort suggestions by score
        self.stdout.write("\nSorting all suggestions by score...")
        sorted_suggestions = sorted(suggestions, key=lambda x: x['score'], reverse=True)

        # 7. Save suggestions to a file
        output_path = 'api/data/suggested_category_links.json'
        self.stdout.write(f"Saving {len(sorted_suggestions)} suggestions to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_suggestions, f, indent=4)

        self.stdout.write(self.style.SUCCESS("\nSuccessfully generated category suggestions."))
