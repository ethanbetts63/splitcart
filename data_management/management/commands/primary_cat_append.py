from django.core.management.base import BaseCommand
from companies.models import PrimaryCategory, Category
from django.db.models import Q

class Command(BaseCommand):
    help = 'Interactively append categories to a primary category.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Primary Category Append Tool ---"))

        while True:
            # 1. Select Primary Category
            primary_categories = list(PrimaryCategory.objects.all().order_by('name'))
            self.stdout.write("\nAvailable Primary Categories:")
            for i, pc in enumerate(primary_categories):
                self.stdout.write(f"  {i + 1}. {pc.name}")

            try:
                pc_choice = input("\nEnter the number of the Primary Category to append to (or 'q' to quit): ")
                if pc_choice.lower() == 'q':
                    break
                selected_pc_index = int(pc_choice) - 1
                if not (0 <= selected_pc_index < len(primary_categories)):
                    self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                    continue
                primary_category = primary_categories[selected_pc_index]
                self.stdout.write(f"You have selected: {primary_category.name}")
            except (ValueError, IndexError):
                self.stdout.write(self.style.ERROR("Invalid input. Please enter a number."))
                continue

            # 2. Get Search Term
            search_term = input(f"\nEnter a search term to find categories to add to '{primary_category.name}': ")

            # 3. Search for categories
            categories_to_append = Category.objects.filter(
                name__icontains=search_term
            ).exclude(
                primary_category=primary_category
            ).order_by('name')

            if not categories_to_append.exists():
                self.stdout.write(self.style.WARNING(f"No new categories found for search term '{search_term}'."))
                continue

            self.stdout.write("\nFound the following categories:")
            for i, cat in enumerate(categories_to_append):
                self.stdout.write(f"  {i + 1}. {cat.name}")

            # 4. Select Categories to Add
            try:
                cat_choices_str = input("\nEnter the numbers of the categories to add (e.g., 1, 5, 4), or 'a' for all: ")
                if cat_choices_str.lower() == 'a':
                    selected_indices = range(len(categories_to_append))
                else:
                    selected_indices = [int(i.strip()) - 1 for i in cat_choices_str.split(',')]
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid input. Please enter comma-separated numbers."))
                continue

            categories_to_add = []
            for i in selected_indices:
                try:
                    categories_to_add.append(categories_to_append[i])
                except IndexError:
                    self.stdout.write(self.style.WARNING(f"Skipping invalid number: {i + 1}"))
            
            if not categories_to_add:
                self.stdout.write(self.style.WARNING("No valid categories selected."))
                continue

            # 5. Confirm and Update
            self.stdout.write(f"\nYou are about to add the following categories to '{primary_category.name}':")