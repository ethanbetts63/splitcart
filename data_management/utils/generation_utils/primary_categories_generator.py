import os
import pprint
from django.db import transaction
from companies.models import Category, Company, PrimaryCategory
from data_management.data.category_mappings import CATEGORY_MAPPINGS, PRIMARY_CATEGORY_HIERARCHY

EXCLUSIONS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'category_exclusions.py')

class PrimaryCategoriesGenerator:
    def __init__(self, command):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style
        self.exclusions = self._load_exclusions()

    def _load_exclusions(self):
        if not os.path.exists(EXCLUSIONS_FILE):
            return {}
        
        with open(EXCLUSIONS_FILE, 'r') as f:
            content = f.read()
            exclusions = {}
            try:
                exec(content, {'__builtins__': {}}, exclusions)
            except Exception as e:
                # Use command's stderr and style
                self.stdout.write(self.style.ERROR(f"Error loading exclusions file: {e}"))
                return {}
            return exclusions.get('CATEGORY_EXCLUSIONS', {})

    def run(self):
        self._delete_existing_primary_categories()
        self._create_primary_categories()
        self._assign_sub_categories()
        self._assign_primary_categories()
        self.stdout.write(self.style.SUCCESS("Successfully generated primary categories."))

    def _delete_existing_primary_categories(self):
        self.stdout.write("Deleting existing primary category objects...")
        deleted_count, _ = PrimaryCategory.objects.all().delete()
        self.stdout.write(f"Deleted {deleted_count} existing primary category objects.")

    def _create_primary_categories(self):
        self.stdout.write("Creating primary category objects...")
        primary_category_names = set()
        for store_mappings in CATEGORY_MAPPINGS.values():
            primary_category_names.update(store_mappings.values())

        # Also include categories from the hierarchy definition
        for parent, children in PRIMARY_CATEGORY_HIERARCHY.items():
            primary_category_names.add(parent)
            primary_category_names.update(children)

        # Filter out None values before creating objects
        valid_primary_category_names = {name for name in primary_category_names if name is not None}

        for name in valid_primary_category_names:
            PrimaryCategory.objects.get_or_create(name=name)
        self.stdout.write(f"Found {len(valid_primary_category_names)} unique primary categories to create.")

    def _assign_sub_categories(self):
        self.stdout.write("Assigning sub-categories to primary categories...")
        for parent_name, child_names in PRIMARY_CATEGORY_HIERARCHY.items():
            try:
                parent_category = PrimaryCategory.objects.get(name=parent_name)
                for child_name in child_names:
                    try:
                        child_category = PrimaryCategory.objects.get(name=child_name)
                        parent_category.sub_categories.add(child_category)
                    except PrimaryCategory.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Child category '{child_name}' not found for parent '{parent_name}'. Skipping."))
                self.stdout.write(f"Assigned sub-categories for '{parent_name}'.")
            except PrimaryCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Parent category '{parent_name}' not found. Skipping."))

    def _assign_primary_categories(self):
        self.stdout.write("Assigning primary categories to categories...")
        for company_name, mappings in CATEGORY_MAPPINGS.items():
            try:
                company = Company.objects.get(name=company_name)
            except Company.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Company '{company_name}' not found. Skipping."))
                continue

            self.stdout.write(f"Processing company: {company.name}")
            
            categories_to_update = []
            
            with transaction.atomic():
                for i, (store_category_name, primary_category_name) in enumerate(mappings.items()):
                    self.stdout.write(f"  Processing mapping {i+1}/{len(mappings)}: '{store_category_name}' -> '{primary_category_name}'")
                    
                    if primary_category_name is None:
                        continue

                    try:
                        primary_category = PrimaryCategory.objects.get(name=primary_category_name)
                        exclusions_for_primary_cat = self.exclusions.get(primary_category.name, [])

                        store_categories = Category.objects.filter(name=store_category_name, company=company)
                        
                        if not store_categories.exists():
                            self.stdout.write(self.style.WARNING(f"    Category '{store_category_name}' not found for {company.name}. Skipping."))
                            continue

                        for store_category in store_categories:
                            descendants = self._get_all_descendants(store_category, set(), mapped_names=set(mappings.keys()))
                            all_categories_to_process = [store_category] + list(descendants)
                            
                            for category in all_categories_to_process:
                                category_identifier = f"{category.name} ({category.company.name})"
                                
                                # Check against exclusion list
                                if category_identifier in exclusions_for_primary_cat:
                                    self.stdout.write(f"    Skipping excluded category: '{category_identifier}' for '{primary_category.name}'")
                                    continue

                                if category.primary_category != primary_category:
                                    category.primary_category = primary_category
                                    categories_to_update.append(category)

                    except PrimaryCategory.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"    Primary category '{primary_category_name}' not found. This should not happen. Skipping."))
                        continue
                
                if categories_to_update:
                    self.stdout.write(f"  Bulk updating {len(categories_to_update)} categories for {company.name}...")
                    Category.objects.bulk_update(categories_to_update, ['primary_category'])
                    self.stdout.write(f"  Successfully updated categories for {company.name}.")

    def _get_all_descendants(self, category, visited, mapped_names=None):
        descendants = set()
        if category in visited:
            return descendants
        visited.add(category)

        children = category.subcategories.all()
        for child in children:
            # Stop at explicitly-mapped boundaries — the child's own mapping will handle it
            if mapped_names and child.name in mapped_names:
                continue
            if child not in descendants:
                descendants.add(child)
                descendants.update(self._get_all_descendants(child, visited, mapped_names))
        return descendants
