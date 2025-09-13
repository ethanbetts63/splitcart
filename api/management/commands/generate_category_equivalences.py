from django.core.management.base import BaseCommand
from django.db.models import Count
from itertools import combinations
from companies.models import Category

class Command(BaseCommand):
    help = 'Generates equivalence links for Level 0 categories based on shared products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing all existing category equivalence links..."))
        # This clears the through table for the ManyToMany relationship
        Category.equivalent_categories.through.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing links cleared."))

        self.stdout.write("--- Starting Level 0 Category Equivalence Generation ---")
        self.stdout.write("Finding root categories (those with no parents)...")

        # 1. Find all root categories
        root_categories = Category.objects.filter(parents__isnull=True).prefetch_related('products')

        # 2. Group them by company
        categories_by_company = {}
        for category in root_categories:
            if category.company.name not in categories_by_company:
                categories_by_company[category.company.name] = []
            categories_by_company[category.company.name].append(category)

        self.stdout.write(f"Found root categories for {len(categories_by_company)} companies.")

        # 3. Pre-calculate product sets for each root category to optimize
        product_sets = {}
        for category in root_categories:
            product_sets[category.id] = set(p.id for p in category.products.all())

        # 4. Iterate through pairs of companies
        company_names = list(categories_by_company.keys())
        equivalences_created = 0

        for company1_name, company2_name in combinations(company_names, 2):
            self.stdout.write(f"\n--- Comparing {company1_name} and {company2_name} ---")
            for cat1 in categories_by_company[company1_name]:
                for cat2 in categories_by_company[company2_name]:
                    set1 = product_sets[cat1.id]
                    set2 = product_sets[cat2.id]

                    if not set1 or not set2:
                        continue

                    # 5. Calculate Jaccard Similarity
                    intersection_size = len(set1.intersection(set2))
                    union_size = len(set1.union(set2))
                    jaccard_similarity = intersection_size / union_size if union_size > 0 else 0

                    # 6. Link if similarity is above a threshold
                    # We'll start with a threshold of 0.1 (10% overlap)
                    similarity_threshold = 0.1

                    if jaccard_similarity >= similarity_threshold:
                        if not cat1.equivalent_categories.filter(pk=cat2.pk).exists():
                            cat1.equivalent_categories.add(cat2)
                            equivalences_created += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"  - LINKED: '{cat1.name}' ({company1_name}) <=> '{cat2.name}' ({company2_name}) [Score: {jaccard_similarity:.2f}]"
                            )
                        )
        
        if equivalences_created == 0:
            self.stdout.write(self.style.WARNING("\nNo new Level 0 equivalences were found meeting the threshold."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully created {equivalences_created} new Level 0 equivalence links."))
