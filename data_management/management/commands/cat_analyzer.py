import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from companies.models import Category, Company

# --- Primary Categories (Hardcoded) ---
PRIMARY_CATEGORIES = [
    "Fruit", "Veg", "Meat", "Seafood", "Dairy", "Eggs", "Freezer",
    "Snacks", "Pantry", "Non-Alcoholic Drinks", "Alcoholic Drinks",
    "Health and Beauty", "Cleaning", "Pet", "Baby", "Electronics",
    "Bakery", "Garden"
]

# --- Output file for mappings ---
MAPPINGS_FILE = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'category_mappings.py')

class Command(BaseCommand):
    help = 'Helps curate category mappings to primary categories for the top two levels.'

    def add_arguments(self, parser):
        parser.add_argument('--company', type=str, required=True, help='The company to analyze categories for (e.g., Coles).')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

    def _load_existing_mappings(self):
        if not os.path.exists(MAPPINGS_FILE):
            return {}
        
        with open(MAPPINGS_FILE, 'r') as f:
            content = f.read()
            mappings = {}
            try:
                exec(content, {'__builtins__': {}}, mappings)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error loading mappings file: {e}"))
                return {}
            return mappings.get('CATEGORY_MAPPINGS', {})

    def _save_mappings(self, mappings):
        with open(MAPPINGS_FILE, 'w') as f:
            f.write("CATEGORY_MAPPINGS = ")
            f.write(json.dumps(mappings, indent=4))

    def handle(self, *args, **options):
        company_name = options['company']
        
        try:
            company_obj = Company.objects.get(name__iexact=company_name)
        except Company.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Company '{company_name}' not found."))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Finding unmapped top & second-level categories for {company_name} ---"))

        all_mappings = self._load_existing_mappings()
        company_mappings = all_mappings.get(company_name, {})

        all_company_cats = list(Category.objects.filter(company=company_obj).prefetch_related('parents'))
        company_cats_dict = {cat.id: cat for cat in all_company_cats}

        categories_to_process = []
        for cat in all_company_cats:
            if not cat.parents.exists():
                categories_to_process.append(cat)
                continue

            is_second_level = True
            parent_ids = cat.parents.values_list('id', flat=True)
            for p_id in parent_ids:
                parent_obj = company_cats_dict.get(p_id)
                if parent_obj and parent_obj.parents.exists():
                    is_second_level = False
                    break
            if is_second_level:
                categories_to_process.append(cat)

        unmapped_categories = [cat for cat in categories_to_process if cat.name not in company_mappings]
        unmapped_categories.sort(key=lambda x: x.name)

        self.stdout.write(self.style.SUCCESS(f"Found {len(unmapped_categories)} unmapped categories in the top two levels."))

        for i, category in enumerate(unmapped_categories):
            # --- Auto-mapping logic ---
            auto_mapped = False
            category_name_lower = category.name.lower().strip()

            for pc in PRIMARY_CATEGORIES:
                primary_category_lower = pc.lower().strip()

                # Condition A: Exact match
                if category_name_lower == primary_category_lower:
                    company_mappings[category.name] = pc
                    all_mappings[company_name] = company_mappings
                    self.stdout.write(self.style.SUCCESS(f"Auto-mapped '{category.name}' to '{pc}' (Exact Match)"))
                    self._save_mappings(all_mappings)
                    auto_mapped = True
                    break

                # Condition B: Substring match (with exception for drinks)
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

            # --- Manual mapping if auto-mapping fails ---
            self.stdout.write(f"\n------------------------------------------------------------------")
            self.stdout.write(f"Category to Map: [{self.style.SUCCESS(category.name)}] (Remaining: {len(unmapped_categories) - i})")

            self.stdout.write("\nPrimary Categories:")
            for idx, pc in enumerate(PRIMARY_CATEGORIES):
                self.stdout.write(f"{idx+1}. {pc}")
            
            while True:
                choice = input("Enter the number of the correct primary category (or 's' to skip, 'q' to quit): ").strip().lower()
                if choice == 'q':
                    self._save_mappings(all_mappings)
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
                        self._save_mappings(all_mappings) # Immediate save
                        self.stdout.write(self.style.SUCCESS(f"Mapped '{category.name}' to '{selected_primary_category}'"))
                        break
                    else:
                        self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                else:
                    self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', or 'q'."))
        
        self.stdout.write(self.style.SUCCESS("--- Category Analyzer Finished. All categories processed. ---"))
        
        self._save_mappings(all_mappings)
        self.stdout.write(self.style.SUCCESS("--- Category Analyzer Finished. Mappings saved. ---"))
