import os
import msvcrt
import json
import time
import datetime
from itertools import combinations
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, CategoryEquivalence

# --- Robust Helper Functions for Persistence ---

def _load_decision_file(filepath):
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, 'r') as f:
            pairs = json.load(f)
            return set(tuple(sorted(p)) for p in pairs)
    except (json.JSONDecodeError, IOError):
        return set()

def _append_to_decision_file(filepath, id1, id2):
    dir_path = os.path.dirname(filepath)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    existing_pairs_set = _load_decision_file(filepath)
    pair_to_add = tuple(sorted((id1, id2)))

    if pair_to_add not in existing_pairs_set:
        existing_pairs_set.add(pair_to_add)
        list_to_save = [list(p) for p in existing_pairs_set]
        with open(filepath, 'w') as f:
            json.dump(list_to_save, f, indent=4)

NON_MATCH_FILE = 'api/data/analysis/category_non_matches.json'
SKIPPED_FILE = 'api/data/analysis/category_skipped.json'

load_non_matches = lambda: _load_decision_file(NON_MATCH_FILE)
load_skipped = lambda: _load_decision_file(SKIPPED_FILE)
append_non_match = lambda id1, id2: _append_to_decision_file(NON_MATCH_FILE, id1, id2)
append_skipped = lambda id1, id2: _append_to_decision_file(SKIPPED_FILE, id1, id2)


class Command(BaseCommand):
    help = 'Interactively create equivalence rules for Level 0 categories.'

    def handle(self, *args, **options):
        root_categories = Category.objects.filter(parents__isnull=True).prefetch_related('products')
        categories_by_company = {}
        for cat in root_categories:
            categories_by_company.setdefault(cat.company.name, []).append(cat)
        
        product_sets = {cat.id: set(p.id for p in cat.products.all()) for cat in root_categories}
        
        potential_pairs = []
        company_names = list(categories_by_company.keys())
        for comp1, comp2 in combinations(company_names, 2):
            for cat1 in categories_by_company[comp1]:
                for cat2 in categories_by_company[comp2]:
                    set1, set2 = product_sets[cat1.id], product_sets[cat2.id]
                    if not set1 or not set2: continue
                    intersection = set1.intersection(set2)
                    union = set1.union(set2)
                    score = len(intersection) / len(union) if union else 0
                    if score > 0.05:
                        potential_pairs.append({
                            'cat1': cat1, 'cat2': cat2, 'score': score, 'shared_products': intersection
                        })
        
        potential_pairs.sort(key=lambda x: x['score'], reverse=True)

        processed_db_pairs = set()
        for eq in CategoryEquivalence.objects.all():
            processed_db_pairs.add(tuple(sorted((eq.from_category_id, eq.to_category_id))))
        
        non_matches = load_non_matches()
        skipped_pairs = load_skipped()

        pairs_to_review = [
            p for p in potential_pairs 
            if tuple(sorted((p['cat1'].id, p['cat2'].id))) not in processed_db_pairs 
            and tuple(sorted((p['cat1'].id, p['cat2'].id))) not in non_matches
            and tuple(sorted((p['cat1'].id, p['cat2'].id))) not in skipped_pairs
        ]

        if not pairs_to_review:
            self.stdout.write(self.style.SUCCESS("No new category pairs to review."))
            return

        decisions = []
        for i, pair_data in enumerate(pairs_to_review):
            os.system('cls' if os.name == 'nt' else 'clear')
            cat1, cat2, score = pair_data['cat1'], pair_data['cat2'], pair_data['score']

            self.stdout.write(self.style.SUCCESS(f"--- Pair {i + 1} of {len(pairs_to_review)} ---"))
            self.stdout.write(f"A: {self.style.SQL_FIELD(cat1.name)} ({cat1.company.name})\nB: {self.style.SQL_FIELD(cat2.name)} ({cat2.company.name})")
            self.stdout.write(f"Similarity Score: {self.style.HTTP_INFO(f'{score:.2f}')}")
            self.stdout.write("Shared Products:")
            shared_product_ids = pair_data['shared_products']
            from products.models import Product
            shared_products = Product.objects.filter(id__in=list(shared_product_ids)[:5])
            for p in shared_products:
                self.stdout.write(f"  - {p.name}")
            if len(shared_product_ids) > 5:
                self.stdout.write(f"  ...and {len(shared_product_ids) - 5} more.")
            self.stdout.write("-" * 50)

            self.stdout.write(f"  {self.style.SQL_KEYWORD('[1]')} (A -> B) '{cat1.name}' is a SUBSET of '{cat2.name}'")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[2]')} (B -> A) '{cat2.name}' is a SUBSET of '{cat1.name}'")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[3]')} (A <=> B) Mutually EQUIVALENT")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[4]')} Skip")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[5]')} NOT a match")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[q]')} Quit")

            while True:
                self.stdout.write(self.style.HTTP_REDIRECT("\nChoose an option: "), ending="")
                self.stdout.flush()
                choice = msvcrt.getch().decode('utf-8').lower()
                self.stdout.write(choice + '\n')
                if choice in ['1', '2', '3', '4', '5', 'q']:
                    break
                self.stdout.write(self.style.ERROR("Invalid input."))

            if choice == 'q': break
            
            if choice == '4':
                append_skipped(cat1.id, cat2.id)
                self.stdout.write(self.style.SUCCESS("Skipped. This pair will be ignored in future runs."))
            elif choice == '5':
                append_non_match(cat1.id, cat2.id)
                self.stdout.write(self.style.SUCCESS("Marked as not a match. This pair will be ignored in future runs."))
            elif choice == '1':
                decisions.append({'from': cat1.id, 'to': cat2.id, 'type': 'SUB'})
                self.stdout.write(self.style.SUCCESS(f"Decision recorded: {cat1.name} -> {cat2.name}"))
            elif choice == '2':
                decisions.append({'from': cat2.id, 'to': cat1.id, 'type': 'SUB'})
                self.stdout.write(self.style.SUCCESS(f"Decision recorded: {cat2.name} -> {cat1.name}"))
            elif choice == '3':
                decisions.append({'from': cat1.id, 'to': cat2.id, 'type': 'EQ'})
                decisions.append({'from': cat2.id, 'to': cat1.id, 'type': 'EQ'})
                self.stdout.write(self.style.SUCCESS(f"Decision recorded: {cat1.name} <=> {cat2.name}"))
            
        if decisions:
            inbox_dir = 'api/data/category_link_inbox'
            if not os.path.exists(inbox_dir):
                os.makedirs(inbox_dir)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(inbox_dir, f"{timestamp}.json")
            
            with open(filename, 'w') as f:
                json.dump(decisions, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS(f"\nSession finished. {len(decisions)} decisions saved to {filename}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nSession finished. No new decisions were made."))
