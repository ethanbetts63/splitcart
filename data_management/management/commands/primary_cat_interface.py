import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from companies.models import Category, Company

# --- Primary Categories (Hardcoded) ---
PRIMARY_CATEGORIES = [
    "Alcoholic Drinks",
    "Baby",
    "Bakery",
    "Cleaning",
    "Clothing",
    "Dairy",
    "Deals",
    "Eggs",
    "Electronics",
    "Freezer",
    "Fruit",
    "Health and Beauty",
    "Health Foods",
    "Home and Garden",
    "Meat",
    "Miscellaneous",
    "Non-Alcoholic Drinks",
    "Pantry",
    "Pet",
    "Seafood",
    "Snacks",
    "Spices",
    "Sweets",
    "Veg"
]

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
        with open(MAPPINGS_FILE, 'w') as f:
            f.write("CATEGORY_MAPPINGS = ")
            f.write(json.dumps(mappings, indent=4))

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
                            category = Category.objects.prefetch_related('subcategories').get(name=cat_name, company=company_obj)
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
        
        # 2. Collect all children that need potential re-mapping
        categories_to_remap = []
        for parent_cat in misc_parents:
            for child_cat in parent_cat.subcategories.all():
                child_mapping = all_mappings.get(parent_cat.company.name, {}).get(child_cat.name)
                if child_mapping is None or child_mapping == "Miscellaneous":
                    categories_to_remap.append(child_cat)

        # De-duplicate and sort
        if not categories_to_remap:
            self.stdout.write("All children of 'Miscellaneous' categories are already mapped to specific primary categories.")
            return
            
        unique_categories_to_remap = list(set(categories_to_remap))
        unique_categories_to_remap.sort(key=lambda x: (x.company.name, x.name))
        
        self.stdout.write(f"Found {len(unique_categories_to_remap)} child categories to potentially re-map.")

        # 3. Interactive mapping loop
        for i, category in enumerate(unique_categories_to_remap):
            company_name = category.company.name
            
            self.stdout.write(f"\n------------------------------------------------------------------")
            parent_names = ", ".join(p.name for p in category.parents.all())
            self.stdout.write(f"Category to Re-Map: [{self.style.SUCCESS(category.name)}] from Company: [{self.style.WARNING(company_name)}]")
            self.stdout.write(f"(Child of: {parent_names})")

            self.stdout.write("\nPrimary Categories:")
            for idx, pc in enumerate(PRIMARY_CATEGORIES):
                self.stdout.write(f"{idx+1}. {pc}")
            
            while True:
                choice = input("Enter the number of the correct primary category (or 's' to skip, 'q' to quit): ").strip().lower()
                if choice == 'q':
                    self.stdout.write(self.style.SUCCESS("Exiting. Mappings saved."))
                    return
                elif choice == 's':
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
                    self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', or 'q'."))

        self.stdout.write(self.style.SUCCESS("\n--- Finished refining miscellaneous categories. ---"))

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

            self.stdout.write("\nPrimary Categories:")
            for idx, pc in enumerate(PRIMARY_CATEGORIES):
                self.stdout.write(f"{idx+1}. {pc}")
            
            while True:
                choice = input("Enter the number of the correct primary category (or 's' to skip, 'q' to quit): ").strip().lower()
                if choice == 'q':
                    self.stdout.write(self.style.SUCCESS("Exiting. Mappings saved."))
                    return
                elif choice == 's':
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
                    self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', or 'q'."))

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
                    choice = input("Enter the number of the correct primary category (or 's' to skip, 'q' to quit): ").strip().lower()
                    if choice == 'q':
                        self.stdout.write(self.style.SUCCESS("Exiting analyzer. Mappings saved."))
                        return
                    elif choice == 's':
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
                        self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', or 'q'."))
        
        self.stdout.write(self.style.SUCCESS("\n--- Category Analyzer Finished. All companies processed. ---"))
