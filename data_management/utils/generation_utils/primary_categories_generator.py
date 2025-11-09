import os
import sys
from collections import defaultdict
from django.db import transaction
from companies.models import Category, Company, PrimaryCategory
from data_management.data.category_mappings import CATEGORY_MAPPINGS

class PrimaryCategoriesGenerator:
    def __init__(self, command):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style

    def run(self):
        self.stdout.write(self.style.SUCCESS("Generating primary categories..."))
        self._create_primary_categories()
        self._assign_primary_categories()
        self.stdout.write(self.style.SUCCESS("Successfully generated primary categories."))

    def _create_primary_categories(self):
        self.stdout.write("Creating primary category objects...")
        primary_category_names = set()
        for store_mappings in CATEGORY_MAPPINGS.values():
            primary_category_names.update(store_mappings.values())

        for name in primary_category_names:
            PrimaryCategory.objects.get_or_create(name=name)
        self.stdout.write(f"Found {len(primary_category_names)} unique primary categories.")

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
                    try:
                        primary_category = PrimaryCategory.objects.get(name=primary_category_name)
                        
                        # Find all categories with this name for the given company
                        store_categories = Category.objects.filter(name=store_category_name, company=company)
                        
                        if not store_categories.exists():
                            self.stdout.write(self.style.WARNING(f"    Category '{store_category_name}' not found for {company.name}. Skipping."))
                            continue

                        for store_category in store_categories:
                            # Get all descendants
                            descendants = self._get_all_descendants(store_category, set())
                            
                            # Combine the category itself with its descendants
                            all_categories_to_update = [store_category] + list(descendants)
                            
                            for category in all_categories_to_update:
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

    def _get_all_descendants(self, category, visited):
        descendants = set()
        if category in visited:
            return descendants
        visited.add(category)
        
        children = category.subcategories.all()
        for child in children:
            if child not in descendants:
                descendants.add(child)
                descendants.update(self._get_all_descendants(child, visited))
        return descendants
