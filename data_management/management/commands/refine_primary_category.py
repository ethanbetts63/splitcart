import os
import pprint
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, PrimaryCategory

EXCLUSIONS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'category_exclusions.py')

PRIMARY_CATEGORIES = [
    "Alcoholic Drinks", "Baby", "Bakery", "Cleaning", "Clothing", "Dairy", "Deals", "Deli",
    "Eggs", "Electronics", "Freezer", "Garden", "Fruit", "Health and Beauty", "Health Foods",
    "Home ", "International", "Meat", "Miscellaneous", "Non-Alcoholic Drinks",
    "Pantry", "Pet", "Seafood", "Snacks", "Spices", "Sauces", "Sweets", "Veg"
]

class Command(BaseCommand):
    help = 'Refines the categories assigned to a specific primary category.'

    def add_arguments(self, parser):
        parser.add_argument('primary_category_name', type=str, help='The name of the primary category to refine.')

    def _load_exclusions(self):
        if not os.path.exists(EXCLUSIONS_FILE):
            return {}
        
        with open(EXCLUSIONS_FILE, 'r') as f:
            content = f.read()
            exclusions = {}
            try:
                exec(content, {'__builtins__': {}}, exclusions)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error loading exclusions file: {e}"))
                return {}
            return exclusions.get('CATEGORY_EXCLUSIONS', {})

    def _save_exclusions(self, exclusions):
        with open(EXCLUSIONS_FILE, 'w') as f:
            f.write("CATEGORY_EXCLUSIONS = ")
            f.write(pprint.pformat(exclusions, indent=4))

    def handle(self, *args, **options):
        primary_category_name = options['primary_category_name']
        try:
            primary_category = PrimaryCategory.objects.get(name__iexact=primary_category_name)
        except PrimaryCategory.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary category '{primary_category_name}' not found."))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Refining Primary Category: {primary_category.name} ---"))

        all_exclusions = self._load_exclusions()
        exclusions_for_primary_cat = set(all_exclusions.get(primary_category.name, []))

        # Get all categories assigned to this primary category, excluding already known exclusions
        assigned_categories = Category.objects.filter(primary_category=primary_category).select_related('company').prefetch_related('parents')
        
        categories_to_review = []
        for cat in assigned_categories:
            # Create a unique identifier for the category including its company
            category_identifier = f"{cat.name} ({cat.company.name})"
            if category_identifier not in exclusions_for_primary_cat:
                categories_to_review.append(cat)

        if not categories_to_review:
            self.stdout.write(self.style.WARNING("No new categories to review for this primary category."))
            return

        self.stdout.write(f"Found {len(categories_to_review)} categories to review.")

        quit_early = False
        for i, category in enumerate(categories_to_review):
            parent_names = ", ".join(p.name for p in category.parents.all())
            
            self.stdout.write("\n" + "-"*50)
            self.stdout.write(f"Reviewing ({i+1}/{len(categories_to_review)}): {self.style.SUCCESS(category.name)}")
            self.stdout.write(f"Company: {category.company.name}")
            if parent_names:
                self.stdout.write(f"Parents: {parent_names}")

            while True:
                choice = input("(k)eep, (r)emove, (m)ove, (q)uit: ").strip().lower()

                if choice == 'q':
                    quit_early = True
                    break
                
                elif choice == 'k':
                    break

                elif choice == 'r':
                    category_identifier = f"{category.name} ({category.company.name})"
                    
                    # Update exclusions
                    if primary_category.name not in all_exclusions:
                        all_exclusions[primary_category.name] = []
                    
                    if category_identifier not in all_exclusions[primary_category.name]:
                        all_exclusions[primary_category.name].append(category_identifier)
                        all_exclusions[primary_category.name].sort() # Keep it tidy
                        self._save_exclusions(all_exclusions)

                    # Update database
                    category.primary_category = None
                    category.save()
                    
                    self.stdout.write(self.style.WARNING(f"Removed and added to exclusion list: '{category_identifier}'"))
                    break
                
                elif choice == 'm':
                    self.stdout.write("\nAvailable Primary Categories:")
                    for idx, pc_name in enumerate(PRIMARY_CATEGORIES):
                        self.stdout.write(f"{idx+1}. {pc_name}")

                    while True:
                        move_choice = input("Enter number to move to (or 'b' to go back): ").strip().lower()
                        if move_choice == 'b':
                            break
                        if move_choice.isdigit():
                            idx = int(move_choice) - 1
                            if 0 <= idx < len(PRIMARY_CATEGORIES):
                                new_primary_cat_name = PRIMARY_CATEGORIES[idx]
                                try:
                                    new_primary_cat = PrimaryCategory.objects.get(name=new_primary_cat_name)
                                    category.primary_category = new_primary_cat
                                    category.save()
                                    self.stdout.write(self.style.SUCCESS(f"Moved '{category.name}' to '{new_primary_cat_name}'."))
                                except PrimaryCategory.DoesNotExist:
                                    self.stdout.write(self.style.ERROR("Selected primary category not found in database."))
                                break # break from move loop
                            else:
                                self.stdout.write(self.style.ERROR("Invalid number."))
                        else:
                            self.stdout.write(self.style.ERROR("Invalid input."))
                    break # break from main choice loop after handling move
                
                else:
                    self.stdout.write(self.style.ERROR("Invalid choice. Please try again."))
            
            if quit_early:
                break
        
        self.stdout.write(self.style.SUCCESS("\n--- Refinement process complete. ---"))
