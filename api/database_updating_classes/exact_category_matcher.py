import re
import unicodedata
from itertools import combinations
from collections import defaultdict
from companies.models import Category, CategoryLink

class ExactCategoryMatcher:
    def __init__(self, command):
        self.command = command
        self.links_created = 0

    def _clean_value(self, value: str) -> str:
        """ Normalizes a category name for exact matching. """
        if not isinstance(value, str):
            return ""
        value = value.replace('&', 'and') # Replace & with and
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        
        # Remove trailing 's' from words
        words = value.split()
        processed_words = []
        for word in words:
            if word.endswith('s') and len(word) > 1: # Avoid removing 's' from single-letter words or words like 'bus'
                processed_words.append(word[:-1])
            else:
                processed_words.append(word)
        
        words = sorted(list(set(processed_words))) # Use processed_words here
        return "".join(words)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Automatic Exact Category Matcher ---"))
        
        # 1. Fetch all categories and clean their names for exact matching
        all_categories = list(Category.objects.all().prefetch_related('company', 'products')) # Fetch products for Jaccard
        cleaned_groups = defaultdict(list)

        for category in all_categories:
            cleaned_name = self._clean_value(category.name)
            if cleaned_name:
                cleaned_groups[cleaned_name].append(category)

        # 2. Create 'MATCH' links based on exact cleaned name matches
        match_links_to_create = []
        for cleaned_name, group in cleaned_groups.items():
            if len(group) < 2:
                continue

            for cat_a, cat_b in combinations(group, 2):
                if cat_a.company_id == cat_b.company_id:
                    continue
                
                cat_a, cat_b = (cat_a, cat_b) if cat_a.id < cat_b.id else (cat_b, cat_a)
                match_links_to_create.append(
                    CategoryLink(category_a=cat_a, category_b=cat_b, link_type='MATCH')
                )

        if match_links_to_create:
            try:
                created_matches = CategoryLink.objects.bulk_create(match_links_to_create, ignore_conflicts=True)
                self.links_created += len(created_matches)
                self.command.stdout.write(self.command.style.SUCCESS(f"  Automatically created {len(created_matches)} new 'MATCH' links."))
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"  Error bulk creating MATCH links: {e}"))

        # 3. Prepare for Jaccard Similarity calculation for CLOSE and DISTANT relations
        self.command.stdout.write("--- Calculating Jaccard Similarities for CLOSE/DISTANT relations ---")
        product_sets = {cat.id: set(p.id for p in cat.products.all()) for cat in all_categories}
        categories_by_company = defaultdict(list)
        for cat in all_categories: categories_by_company[cat.company.name].append(cat)

        existing_links = set()
        for link in CategoryLink.objects.all():
            existing_links.add(tuple(sorted((link.category_a_id, link.category_b_id))))

        close_distant_links_to_create = []
        company_names = list(categories_by_company.keys())

        for company1_name, company2_name in combinations(company_names, 2):
            cat_list1 = categories_by_company[company1_name]
            cat_list2 = categories_by_company[company2_name]

            for cat1 in cat_list1:
                for cat2 in cat_list2:
                    # Ensure they are from different companies (already handled by combinations, but good check)
                    if cat1.company_id == cat2.company_id:
                        continue
                    
                    # Sort by ID for consistent key for existing_links check
                    sorted_cat_ids = tuple(sorted((cat1.id, cat2.id)))
                    if sorted_cat_ids in existing_links:
                        continue # Skip if already linked

                    set1 = product_sets.get(cat1.id, set())
                    set2 = product_sets.get(cat2.id, set())

                    if not set1 or not set2: # Skip if either category has no products
                        continue

                    intersection_size = len(set1.intersection(set2))
                    if intersection_size == 0: # Skip if no shared products
                        continue

                    union_size = len(set1.union(set2))
                    jaccard_similarity = intersection_size / union_size if union_size > 0 else 0

                    if jaccard_similarity >= 0.80:
                        close_distant_links_to_create.append(
                            CategoryLink(category_a=cat1, category_b=cat2, link_type='CLOSE')
                        )
                    elif jaccard_similarity >= 0.60:
                        close_distant_links_to_create.append(
                            CategoryLink(category_a=cat1, category_b=cat2, link_type='DISTANT')
                        )
        
        if close_distant_links_to_create:
            try:
                created_close_distant = CategoryLink.objects.bulk_create(close_distant_links_to_create, ignore_conflicts=True)
                
                close_count = sum(1 for link in created_close_distant if link.link_type == 'CLOSE')
                distant_count = sum(1 for link in created_close_distant if link.link_type == 'DISTANT')

                self.links_created += len(created_close_distant)
                if close_count > 0:
                    self.command.stdout.write(self.command.style.SUCCESS(f"  Automatically created {close_count} new 'CLOSE' links."))
                if distant_count > 0:
                    self.command.stdout.write(self.command.style.SUCCESS(f"  Automatically created {distant_count} new 'DISTANT' links."))
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"  Error bulk creating CLOSE/DISTANT links: {e}"))

        if self.links_created == 0:
            self.command.stdout.write("No new automatic matches found.")
        else:
            self.command.stdout.write(self.command.style.SUCCESS(f"Total automatic links created: {self.links_created}"))
