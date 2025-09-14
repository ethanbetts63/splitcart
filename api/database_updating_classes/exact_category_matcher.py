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
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        words = sorted(list(set(value.split())))
        return "".join(words)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Automatic Exact Category Matcher ---"))
        
        # 1. Fetch all categories and clean their names
        all_categories = Category.objects.all().prefetch_related('company')
        cleaned_groups = defaultdict(list)

        for category in all_categories:
            cleaned_name = self._clean_value(category.name)
            if cleaned_name:
                cleaned_groups[cleaned_name].append(category)

        # 2. Find groups with multiple categories from different companies
        links_to_create = []
        for cleaned_name, group in cleaned_groups.items():
            if len(group) < 2:
                continue

            # 3. Create pairs and check if a link needs to be created
            for cat_a, cat_b in combinations(group, 2):
                # Ensure they are from different companies
                if cat_a.company_id == cat_b.company_id:
                    continue
                
                # Sort by ID to ensure consistency for the database constraint
                cat_a, cat_b = (cat_a, cat_b) if cat_a.id < cat_b.id else (cat_b, cat_a)

                links_to_create.append(
                    CategoryLink(category_a=cat_a, category_b=cat_b, link_type='MATCH')
                )

        if not links_to_create:
            self.command.stdout.write("No new automatic matches found.")
            return

        # 4. Bulk create the new links, ignoring any that violate the unique constraint
        try:
            created_links = CategoryLink.objects.bulk_create(links_to_create, ignore_conflicts=True)
            self.links_created = len(created_links)
            self.command.stdout.write(self.command.style.SUCCESS(f"  Automatically created {self.links_created} new 'MATCH' links."))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"  Error bulk creating links: {e}"))
