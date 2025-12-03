import os
import json
import pprint
from django.conf import settings
from django.core.management.base import BaseCommand
from companies.models import Category, Company

# --- Primary Categories (Hardcoded) ---
PRIMARY_CATEGORIES = [
    "Miscellaneous",
    "Alcoholic Drinks",
    "Baby",
    "Bakery",
    "Beauty",
    "Beef",
    "Cakes",
    "Cheese",
    "Chicken",
    "Chocolate",
    "Cleaning",
    "Dairy",
    "Deals",
    "Deli",
    "Eggs",
    "Freezer",
    "Fruit",
    "Garden",
    "Health",
    "Health Foods",
    "Home",
    "Ice-Cream",
    "International",
    "Lamb",
    "Lollies",
    "Meat",
    "Milk",
    "Non-Alcoholic Drinks",
    "Pantry",
    "Pet",
    "Pork",
    "Seafood",
    "Snacks",
    "Spices",
    "Sauces",
    "Sweets",
    "Veg",
    "Yogurt"
]
"""
secondary categories are added as needed for the categories with a lot of products

Dairy: "Cheese", "Milk", "Yogurt"
Meat: "Beef", "Chicken", "Pork", "Lamb"
Freezer: "Ice-Cream", 
Sweets: "Chocolate", "Lollies", "Cakes"

"""


# --- Output file for mappings ---
MAPPINGS_FILE = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'category_mappings.py')

class Command(BaseCommand):
    help = 'Helps curate category mappings to primary categories for the top two levels of all companies.'

    def add_arguments(self, parser):
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')
        parser.add_argument('--unattached', action='store_true', help='Iterate through all categories with no primary category attached.')
        parser.add_argument('--refine-misc', action='store_true', help='Iterate through children of "Miscellaneous" categories to refine them.')

    def _load_existing_mappings(self):
        if not os.path.exists(MAPPINGS_FILE):
            return {}
        
        with open(MAPPINGS_FILE, 'r') as f:
            content = f.read()
            mappings = {}
            try:
                # Use exec to read the dictionary from the Python file
                exec(content, {'__builtins__': {}}, mappings)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error loading mappings file: {e}"))
                return {}
            return mappings.get('CATEGORY_MAPPINGS', {})

    def _save_mappings(self, mappings):
        # Preserve the existing hierarchy if it exists
        hierarchy = {}
        if os.path.exists(MAPPINGS_FILE):
            with open(MAPPINGS_FILE, 'r') as f:
                content = f.read()
                try:
                    # Execute content in a scope to get both dictionaries
                    file_scope = {}
                    exec(content, {'__builtins__': {}}, file_scope)
                    if 'PRIMARY_CATEGORY_HIERARCHY' in file_scope:
                        hierarchy = file_scope['PRIMARY_CATEGORY_HIERARCHY']
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Could not preserve PRIMARY_CATEGORY_HIERARCHY: {e}"))

        with open(MAPPINGS_FILE, 'w') as f:
            f.write("CATEGORY_MAPPINGS = ")
            f.write(pprint.pformat(mappings, indent=4))
            f.write("\n\n")
            f.write("PRIMARY_CATEGORY_HIERARCHY = ")
            f.write(pprint.pformat(hierarchy, indent=4))

    def _handle_refine_misc(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Refining "Miscellaneous" Categories ---'))
        
        all_mappings = self._load_existing_mappings()
        
        # 1. Find all categories mapped to "Miscellaneous" that have children
        misc_parents = []
        for company_name, mappings in all_mappings.items():
            try:
                company_obj = Company.objects.get(name=company_name)
                for cat_name, primary_cat_name in mappings.items():
                    if primary_cat_name == "Miscellaneous":
                        try:
                            category = Category.objects.prefetch_related('subcategories', 'parents', 'company').get(name=cat_name, company=company_obj)
                            if category.subcategories.exists():
                                misc_parents.append(category)
                        except Category.DoesNotExist:
                            continue
            except Company.DoesNotExist:
                continue
        
        if not misc_parents:
            self.stdout.write("No 'Miscellaneous' categories with subcategories found to refine.")
            return

        self.stdout.write(f"Found {len(misc_parents)} 'Miscellaneous' categories with children to refine.")
        
        # 2. Loop through each parent one by one
        for parent_cat in misc_parents:
            company_name = parent_cat.company.name
            company_mappings = all_mappings.get(company_name, {})

            # Find children of this specific parent that need mapping
            children_to_map = []
            for child_cat in parent_cat.subcategories.all():
                if child_cat.name not in company_mappings or company_mappings.get(child_cat.name) == "Miscellaneous":
                    children_to_map.append(child_cat)
            
            if not children_to_map:
                self.stdout.write(f"\nAll children of '{parent_cat.name}' are already specifically mapped. Ignoring parent.")
                all_mappings[company_name][parent_cat.name] = None
                self._save_mappings(all_mappings)
                continue

            self.stdout.write(f"\n--- Refining children of '{parent_cat.name}' ({company_name}) ---")
            
            # 3. Inner loop for the children of the current parent
            total_children = len(children_to_map)
            quit_early = False
            for i, child_category in enumerate(children_to_map):
                
                # --- Auto-mapping logic ---
                auto_mapped = False
                category_name_lower = child_category.name.lower().strip()

                for mapped_name, primary_cat in company_mappings.items():
                    if primary_cat is None: continue
                    if category_name_lower == mapped_name.lower().strip():
                        all_mappings[company_name][child_category.name] = primary_cat
                        self._save_mappings(all_mappings)
                        self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{child_category.name}' to '{primary_cat}' (Match with existing mapping: '{mapped_name}')"))
                        auto_mapped = True
                        break
                
                if auto_mapped: continue

                for pc in PRIMARY_CATEGORIES:
                    primary_category_lower = pc.lower().strip()
                    if category_name_lower == primary_category_lower:
                        all_mappings[company_name][child_category.name] = pc
                        self._save_mappings(all_mappings)
                        self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{child_category.name}' to '{pc}' (Exact Match)"))
                        auto_mapped = True
                        break

                if auto_mapped: continue
                # --- End of auto-mapping logic ---

                self.stdout.write(f"\n------------------------------------------------------------------")
                parent_names = ", ".join(p.name for p in child_category.parents.all())
                self.stdout.write(f"Category: [{self.style.SUCCESS(child_category.name)}] Company: [{self.style.WARNING(company_name)}]")
                self.stdout.write(f"(Child of: {parent_names}) (Remaining: {total_children - i})")

                self.stdout.write("Primary Categories:")
                for idx, pc in enumerate(PRIMARY_CATEGORIES):
                    self.stdout.write(f"{idx+1}. {pc}")

                while True:
                    choice = input("Num or 's'/skip, 'i'/ignore, 'q'/quit): ").strip().lower()
                    if choice == 'q':
                        quit_early = True
                        break
                    elif choice == 's':
                        break
                    elif choice == 'i':
                        if company_name not in all_mappings: all_mappings[company_name] = {}
                        all_mappings[company_name][child_category.name] = None
                        self._save_mappings(all_mappings)
                        self.stdout.write(self.style.WARNING(f"Permanently ignoring '{child_category.name}' for company {company_name}."))
                        break
                    elif choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(PRIMARY_CATEGORIES):
                            selected_primary_category = PRIMARY_CATEGORIES[idx]
                            if company_name not in all_mappings: all_mappings[company_name] = {}
                            all_mappings[company_name][child_category.name] = selected_primary_category
                            self._save_mappings(all_mappings)
                            self.stdout.write(self.style.SUCCESS(f"Mapped '{child_category.name}' to '{selected_primary_category}' for company {company_name}."))
                            break
                        else:
                            self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                    else:
                        self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', 'i', or 'q'."))
                if quit_early:
                    break
            
            if quit_early:
                self.stdout.write(self.style.SUCCESS("Exiting refinement process. Mappings saved."))
                return

            # 4. After the inner loop finishes, update the parent
            self.stdout.write(f"\nFinished refining children for '{parent_cat.name}'.")
            self.stdout.write(f"Setting parent category '{parent_cat.name}' to be permanently ignored.")
            
            if company_name not in all_mappings:
                all_mappings[company_name] = {}
            all_mappings[company_name][parent_cat.name] = None
            self._save_mappings(all_mappings)

        self.stdout.write(self.style.SUCCESS("\n--- Finished refining all miscellaneous categories. ---"))

    def _handle_unattached(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Processing Unattached Categories ---'))
        
        all_mappings = self._load_existing_mappings()
        
        # Get all categories that don't have a primary category assigned
        unattached_categories = list(Category.objects.filter(primary_category__isnull=True).select_related('company').order_by('company__name', 'name'))
        
        if not unattached_categories:
            self.stdout.write("No unattached categories found.")
            return

        self.stdout.write(f"Found {len(unattached_categories)} categories not assigned to any Primary Category.")

        for i, category in enumerate(unattached_categories):
            company_name = category.company.name
            
            # Check if a mapping for this category name already exists for the company.
            if category.name in all_mappings.get(company_name, {}):
                continue

            self.stdout.write(f"\n------------------------------------------------------------------")
            self.stdout.write(f"Category to Map: [{self.style.SUCCESS(category.name)}] from Company: [{self.style.WARNING(company_name)}] (Remaining: {len(unattached_categories) - i})")

            for idx, pc in enumerate(PRIMARY_CATEGORIES):
                self.stdout.write(f"{idx+1}. {pc}")
            
            while True:
                choice = input("Enter the number of the correct primary category (or 's' to skip, 'i' to permanently ignore, 'q' to quit): ").strip().lower()
                if choice == 'q':
                    self.stdout.write(self.style.SUCCESS("Exiting. Mappings saved."))
                    return
                elif choice == 's':
                    break
                elif choice == 'i':
                    if company_name not in all_mappings:
                        all_mappings[company_name] = {}
                    all_mappings[company_name][category.name] = None
                    self._save_mappings(all_mappings)
                    self.stdout.write(self.style.WARNING(f"Permanently ignoring '{category.name}' for company {company_name}."))
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(PRIMARY_CATEGORIES):
                        selected_primary_category = PRIMARY_CATEGORIES[idx]
                        
                        if company_name not in all_mappings:
                            all_mappings[company_name] = {}
                        
                        all_mappings[company_name][category.name] = selected_primary_category
                        
                        self._save_mappings(all_mappings)
                        self.stdout.write(self.style.SUCCESS(f"Mapped '{category.name}' to '{selected_primary_category}' for company {company_name}."))
                        break
                    else:
                        self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                else:
                    self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', 'i', or 'q'."))

        self.stdout.write(self.style.SUCCESS("\n--- Finished processing unattached categories. ---"))


    def handle(self, *args, **options):
        if options['unattached']:
            self._handle_unattached(*args, **options)
            return
        if options['refine_misc']:
            self._handle_refine_misc(*args, **options)
            return

        all_mappings = self._load_existing_mappings()
        all_companies = Company.objects.all()
        all_categories = list(Category.objects.all().prefetch_related('parents'))
        all_categories_dict = {cat.id: cat for cat in all_categories}

        for company_obj in all_companies:
            company_name = company_obj.name
            self.stdout.write(self.style.SUCCESS(f"\n--- Processing Company: {company_name} ---"))

            company_mappings = all_mappings.get(company_name, {})
            company_cats = [cat for cat in all_categories if cat.company_id == company_obj.id]

            categories_to_process = []
            for cat in company_cats:
                if not cat.parents.exists():
                    categories_to_process.append(cat)
                    continue

                is_second_level = True
                parent_ids = cat.parents.values_list('id', flat=True)
                for p_id in parent_ids:
                    parent_obj = all_categories_dict.get(p_id)
                    if parent_obj and parent_obj.parents.exists():
                        is_second_level = False
                        break
                if is_second_level:
                    categories_to_process.append(cat)

            unmapped_categories = [cat for cat in categories_to_process if cat.name not in company_mappings]
            unmapped_categories.sort(key=lambda x: x.name)

            if not unmapped_categories:
                self.stdout.write(f"No unmapped categories found for {company_name}.")
                continue

            self.stdout.write(self.style.SUCCESS(f"Found {len(unmapped_categories)} unmapped categories in the top two levels for {company_name}."))

            for i, category in enumerate(unmapped_categories):
                auto_mapped = False
                category_name_lower = category.name.lower().strip()

                for mapped_name, primary_cat in company_mappings.items():
                    if primary_cat is None: continue
                    if category_name_lower == mapped_name.lower().strip():
                        company_mappings[category.name] = primary_cat
                        all_mappings[company_name] = company_mappings
                        self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{category.name}' to '{primary_cat}' (Match with existing mapping: '{mapped_name}')"))
                        self._save_mappings(all_mappings)
                        auto_mapped = True
                        break
                
                if auto_mapped:
                    continue

                for pc in PRIMARY_CATEGORIES:
                    primary_category_lower = pc.lower().strip()
                    if category_name_lower == primary_category_lower:
                        company_mappings[category.name] = pc
                        all_mappings[company_name] = company_mappings
                        self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{category.name}' to '{pc}' (Exact Match)"))
                        self._save_mappings(all_mappings)
                        auto_mapped = True
                        break

                    is_drink_category = "drink" in primary_category_lower
                    if primary_category_lower in category_name_lower and not is_drink_category:
                        company_mappings[category.name] = pc
                        all_mappings[company_name] = company_mappings
                        self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{category.name}' to '{pc}' (Substring Match)"))
                        self._save_mappings(all_mappings)
                        auto_mapped = True
                        break
                
                if auto_mapped:
                    continue

                self.stdout.write(f"\n------------------------------------------------------------------")
                self.stdout.write(f"Category to Map: [{self.style.SUCCESS(category.name)}] (Remaining: {len(unmapped_categories) - i})")

                self.stdout.write("\nPrimary Categories:")
                for idx, pc in enumerate(PRIMARY_CATEGORIES):
                    self.stdout.write(f"{idx+1}. {pc}")
                
                while True:
                    choice = input("Enter the number of the correct primary category (or 's' to skip, 'i' to permanently ignore, 'q' to quit): ").strip().lower()
                    if choice == 'q':
                        self.stdout.write(self.style.SUCCESS("Exiting analyzer. Mappings saved."))
                        return
                    elif choice == 's':
                        break
                    elif choice == 'i':
                        if company_name not in all_mappings:
                            all_mappings[company_name] = {}
                        all_mappings[company_name][category.name] = None
                        self._save_mappings(all_mappings)
                        self.stdout.write(self.style.WARNING(f"Permanently ignoring '{category.name}' for company {company_name}."))
                        break
                    elif choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(PRIMARY_CATEGORIES):
                            selected_primary_category = PRIMARY_CATEGORIES[idx]
                            company_mappings[category.name] = selected_primary_category
                            all_mappings[company_name] = company_mappings
                            self._save_mappings(all_mappings)
                            self.stdout.write(self.style.SUCCESS(f"Mapped '{category.name}' to '{selected_primary_category}'"))
                            break
                        else:
                            self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                    else:
                        self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', 'i', or 'q'."))
        
        self.stdout.write(self.style.SUCCESS("\n--- Category Analyzer Finished. All companies processed. ---"))

