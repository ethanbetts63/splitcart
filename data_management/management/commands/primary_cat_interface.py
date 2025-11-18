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
    "Garden",
    "Health and Beauty",
    "Health Foods",
    "Household",
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
