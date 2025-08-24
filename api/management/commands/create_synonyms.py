import os
import msvcrt
from django.core.management.base import BaseCommand
from api.utils.management_utils.synonym_tool import (
    load_existing_synonyms,
    load_non_matches,
    load_unsure_matches,
    read_brand_matches,
    append_synonym,
    append_non_match,
    append_unsure_match,
)

class Command(BaseCommand):
    help = 'Interactively create a brand synonym dictionary from a list of potential matches.'

    def handle(self, *args, **options):
        # Load all existing data
        processed_brands = load_existing_synonyms()
        non_matches = load_non_matches()
        unsure_matches = load_unsure_matches()
        all_matches = read_brand_matches()

        if not all_matches:
            self.stdout.write(self.style.WARNING("'brand_matches.csv' not found or is empty. Please run 'find_brand_matches' first."))
            return

        # Filter out pairs that have already been decided to get an accurate progress count
        matches_to_review = []
        for match in all_matches:
            brand1, _, brand2, _, _ = match
            if brand1 in processed_brands or brand2 in processed_brands:
                continue
            canonical_pair = tuple(sorted((brand1, brand2)))
            if canonical_pair in non_matches or canonical_pair in unsure_matches:
                continue
            matches_to_review.append(match)

        total_to_review = len(matches_to_review)
        if total_to_review == 0:
            self.stdout.write(self.style.SUCCESS("No new brand matches to review."))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting synonym creation tool. {total_to_review} pairs to review."))

        for i, match in enumerate(matches_to_review):
            brand1, example1, brand2, example2, score = match

            # Clear screen for clean UI
            os.system('cls' if os.name == 'nt' else 'clear')

            self.stdout.write(f"--- Pair {i + 1} of {total_to_review} ---")
            self.stdout.write(f"Match Score: {score}")
            self.stdout.write(f"  [1] {brand1} (e.g., '{example1}')")
            self.stdout.write(f"  [2] {brand2} (e.g., '{example2}')")
            self.stdout.write("-" * 50)

            # --- Main Prompt ---
            self.stdout.write("Please choose an option:")
            self.stdout.write(f"  [1] '{brand1}' is canonical")
            self.stdout.write(f"  [2] '{brand2}' is canonical")
            self.stdout.write("  [3] Unsure")
            self.stdout.write("  [4] No Match")
            self.stdout.write("  [q] Quit")
            while True:
                self.stdout.write("Your choice: ", ending="")
                self.stdout.flush()
                char = msvcrt.getch().decode('utf-8').lower()
                self.stdout.write(char + '\n') # Echo character and move to next line
                choice = char
                if choice in ['1', '2', '3', '4', 'q']:
                    break
                self.stdout.write(self.style.ERROR("Invalid input."))

            if choice == 'q':
                break
            
            # Get the canonical pair once for use in multiple places
            canonical_pair = tuple(sorted((brand1, brand2)))

            if choice == '4': # No Match
                append_non_match(brand1, brand2)
                non_matches.add(canonical_pair)
                continue
            
            if choice == '3': # Unsure
                append_unsure_match(brand1, brand2)
                unsure_matches.add(canonical_pair)
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
