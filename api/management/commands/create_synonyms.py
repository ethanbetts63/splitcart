import os
from django.core.management.base import BaseCommand
from api.utils.management_utils.synonym_tool import (
    load_existing_synonyms,
    read_brand_matches,
    append_synonym,
)

class Command(BaseCommand):
    help = 'Interactively create a brand synonym dictionary from a list of potential matches.'

    def handle(self, *args, **options):
        # Load existing data
        synonyms, processed_brands = load_existing_synonyms()
        matches = read_brand_matches()

        if not matches:
            self.stdout.write(self.style.WARNING("'brand_matches.csv' not found or is empty. Please run 'find_brand_matches' first."))
            return

        self.stdout.write(self.style.SUCCESS("Starting synonym creation tool..."))

        for match in matches:
            brand1, example1, brand2, example2, score = match

            # Skip if either brand has already been processed
            if brand1 in processed_brands or brand2 in processed_brands:
                continue

            # Clear screen for clean UI
            os.system('cls' if os.name == 'nt' else 'clear')

            self.stdout.write("-" * 50)
            self.stdout.write(f"Match Score: {score}")
            self.stdout.write(f"  [1] {brand1} (e.g., '{example1}')")
            self.stdout.write(f"  [2] {brand2} (e.g., '{example2}')")
            self.stdout.write("-" * 50)

            # --- Simplified Prompt ---
            while True:
                choice = input("Choose the canonical brand [1, 2], or (n)o match, (q)uit: ").lower()
                if choice in ['1', '2', 'n', 'q']:
                    break
                self.stdout.write(self.style.ERROR("Invalid input. Please enter 1, 2, n, or q."))

            if choice == 'q':
                break
            if choice == 'n':
                continue

            # If choice is '1' or '2', they are a match
            if choice == '1':
                canonical, synonym = brand1, brand2
            else: # choice == '2'
                canonical, synonym = brand2, brand1

            # Append to file and update processed list
            if append_synonym(synonym, canonical):
                self.stdout.write(self.style.SUCCESS(f"Mapped '{synonym}' -> '{canonical}'"))
                processed_brands.add(synonym)
                processed_brands.add(canonical)
            else:
                self.stderr.write(self.style.ERROR("Failed to write to synonym file."))

        self.stdout.write(self.style.SUCCESS("Synonym creation session finished."))
