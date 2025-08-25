import os
import msvcrt
from django.core.management.base import BaseCommand
from api.utils.management_utils.synonym_tool import (
    load_existing_synonyms,
    load_non_matches,
    load_unsure_matches,
    load_rule_based_matches,
    read_brand_matches,
    append_synonym,
    append_non_match,
    append_unsure_match,
    append_rule_based_match,
)
from products.models import Product

import csv
import json

def load_brand_rules():
    path = 'api/data/analysis/brand_rules.json'
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)

def save_brand_rules(rules):
    path = 'api/data/analysis/brand_rules.json'
    with open(path, 'w') as f:
        json.dump(rules, f, indent=4)

def read_rule_based_matches():
    path = 'api/data/analysis/brand_rule_based_matches.csv'
    if not os.path.exists(path):
        return []
    with open(path, 'r', newline='') as f:
        reader = csv.reader(f)
        return [tuple(row) for row in reader if row]

class Command(BaseCommand):
    help = 'Interactively create conditional brand rules from a list of potential matches.'

    def handle(self, *args, **options):
        brand_rules = load_brand_rules()
        rule_based_matches = read_rule_based_matches()

        # Load existing decisions to avoid re-processing
        processed_synonyms = load_existing_synonyms()
        non_matches = load_non_matches()
        unsure_matches = load_unsure_matches()
        existing_rules = load_brand_rules()

        # Create a set of already processed rule pairs for quick lookup
        processed_rule_pairs = set()
        for rule in existing_rules:
            processed_rule_pairs.add(tuple(sorted(rule["brands"])))

        matches_to_review = []
        for brand1, brand2 in rule_based_matches:
            # Check if already processed as a simple synonym
            if brand1 in processed_synonyms or brand2 in processed_synonyms:
                continue
            canonical_pair = tuple(sorted((brand1, brand2)))
            # Check if already processed as a non-match or unsure
            if canonical_pair in non_matches or canonical_pair in unsure_matches:
                continue
            # Check if already processed as a rule
            if canonical_pair in processed_rule_pairs:
                continue
            matches_to_review.append((brand1, brand2))

        if not matches_to_review:
            self.stdout.write(self.style.SUCCESS("No new rule-based matches to review."))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting brand rule creation tool. {len(matches_to_review)} pairs to review."))

        for i, (brand1, brand2) in enumerate(matches_to_review):
            os.system('cls' if os.name == 'nt' else 'clear')

            self.stdout.write(self.style.SUCCESS(f"--- Pair {i + 1} of {len(matches_to_review)} ---"))
            self.stdout.write(f"Comparing Brands: {self.style.SQL_FIELD(brand1)} vs. {self.style.SQL_FIELD(brand2)}")
            self.stdout.write("-" * 50)

            # --- Main Prompt ---
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[1]')} '{brand1}' canonical IF product name contains")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[2]')} '{brand2}' canonical IF product name contains")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[3]')} '{brand1}' is canonical")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[4]')} '{brand2}' is canonical")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[5]')} custom canonical")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[6]')} Not match")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[7]')} Skip")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[q]')} Quit")

            # --- Product Display ---
            self.stdout.write("-" * 50)
            self.stdout.write(self.style.HTTP_INFO(f"Products for [{self.style.SUCCESS(brand1)}]:"))
            products1 = Product.objects.filter(brand__iexact=brand1)
            if products1:
                for p in products1:
                    self.stdout.write(f"  - {self.style.SQL_KEYWORD('Name:')} {p.name}, {self.style.SQL_KEYWORD('Size:')} {p.sizes}")
            else:
                self.stdout.write(self.style.WARNING("  No products found."))

            self.stdout.write(self.style.HTTP_INFO(f"\nProducts for [{self.style.SUCCESS(brand2)}]:"))
            products2 = Product.objects.filter(brand__iexact=brand2)
            if products2:
                for p in products2:
                    self.stdout.write(f"  - {self.style.SQL_KEYWORD('Name:')} {p.name}, {self.style.SQL_KEYWORD('Size:')} {p.sizes}")
            else:
                self.stdout.write(self.style.WARNING("  No products found."))
            self.stdout.write("-" * 50)

            while True:
                self.stdout.write(self.style.HTTP_REDIRECT("\nChoose an option: "), ending="")
                self.stdout.flush()
                char = msvcrt.getch().decode('utf-8').lower()
                self.stdout.write(char + '\n')
                choice = char
                if choice in ['1', '2', '3', '4', '5', '6', '7', 'q']:
                    break
                self.stdout.write(self.style.ERROR("Invalid input."))

            if choice == 'q':
                break

            canonical_pair = tuple(sorted((brand1, brand2)))

            if choice in ['1', '2']:
                keywords_input = input("Enter the keyword(s) to look for in the product name (comma-separated): ").strip()
                if keywords_input:
                    keywords = [k.strip() for k in keywords_input.split(',')]
                    canonical_brand = brand1 if choice == '1' else brand2
                    rule = {
                        "brands": [brand1, brand2],
                        "canonical_brand": canonical_brand,
                        "condition_type": "name_contains_any",
                        "condition_values": keywords
                    }
                    brand_rules.append(rule)
                    save_brand_rules(brand_rules)
                    self.stdout.write(self.style.SUCCESS(f"Rule created and saved: {rule}"))
                else:
                    self.stdout.write(self.style.WARNING("Keywords cannot be empty. No rule created."))
            
            elif choice == '3':
                append_synonym(brand2, brand1)
                self.stdout.write(self.style.SUCCESS(f"Mapped '{brand2}' -> '{brand1}'"))

            elif choice == '4':
                append_synonym(brand1, brand2)
                self.stdout.write(self.style.SUCCESS(f"Mapped '{brand1}' -> '{brand2}'"))

            elif choice == '5':
                custom_canonical = input("Enter custom canonical name: ").strip()
                if custom_canonical:
                    append_synonym(brand1, custom_canonical)
                    append_synonym(brand2, custom_canonical)
                    self.stdout.write(self.style.SUCCESS(f"Mapped '{brand1}' and '{brand2}' -> '{custom_canonical}'"))
                else:
                    self.stdout.write(self.style.WARNING("Custom canonical name cannot be empty."))

            elif choice == '6':
                append_non_match(brand1, brand2)
                self.stdout.write(self.style.SUCCESS("Marked as not a match."))

            elif choice == '7':
                append_unsure_match(brand1, brand2)
                self.stdout.write(self.style.SUCCESS("Marked as unsure."))

        self.stdout.write(self.style.SUCCESS("Brand rule creation session finished."))
