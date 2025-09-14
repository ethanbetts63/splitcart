import os
import msvcrt
import json
import time
import datetime
from itertools import combinations
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, CategoryEquivalence

# --- Persistence Helper Functions (same as before) ---
def _load_decision_file(filepath):
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, 'r') as f:
            return set(tuple(sorted(p)) for p in json.load(f))
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
        with open(filepath, 'w') as f:
            json.dump([list(p) for p in existing_pairs_set], f, indent=4)

NON_MATCH_FILE = 'api/data/analysis/category_non_matches.json'
SKIPPED_FILE = 'api/data/analysis/category_skipped.json'
load_non_matches = lambda: _load_decision_file(NON_MATCH_FILE)
load_skipped = lambda: _load_decision_file(SKIPPED_FILE)
append_non_match = lambda id1, id2: _append_to_decision_file(NON_MATCH_FILE, id1, id2)
append_skipped = lambda id1, id2: _append_to_decision_file(SKIPPED_FILE, id1, id2)


class Command(BaseCommand):
    help = 'Interactively create equivalence rules for categories at a specific nesting level.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level', type=int, required=True,
            help='The category nesting level to process (0 for roots, 1 for their children, etc.).'
        )

    def _calculate_levels(self):
        self.stdout.write("Calculating category levels...")
        levels = {}
        current_level = 0
        level_cats = list(Category.objects.filter(parents__isnull=True))
        processed_cats = set()

        while level_cats:
            next_level_cats = set()
            for cat in level_cats:
                if cat.id not in processed_cats:
                    levels[cat.id] = current_level
                    processed_cats.add(cat.id)
                    for sub_cat in cat.subcategories.all():
                        next_level_cats.add(sub_cat)
            level_cats = list(next_level_cats)
            current_level += 1
        self.stdout.write("Level calculation complete.")
        return levels

    def handle(self, *args, **options):
        level_to_process = options['level']
        
        category_levels = self._calculate_levels()
        categories_at_level = [cat_id for cat_id, lvl in category_levels.items() if lvl == level_to_process]
        
        all_cats = Category.objects.filter(id__in=categories_at_level).prefetch_related('products', 'company', 'parents')
        product_sets = {cat.id: set(p.id for p in cat.products.all()) for cat in all_cats}

        potential_pairs = []

        if level_to_process == 0:
            self.stdout.write("--- Generating pairs for Level 0 (Root Categories) ---")
            cats_by_comp = defaultdict(list)
            for cat in all_cats: cats_by_comp[cat.company_id].append(cat)
            for comp1, comp2 in combinations(cats_by_comp.keys(), 2):
                for cat1 in cats_by_comp[comp1]:
                    for cat2 in cats_by_comp[comp2]:
                        potential_pairs.append((cat1, cat2))
        else:
            self.stdout.write(f"--- Generating pairs for Level {level_to_process} (Child Categories) ---")
            parent_level = level_to_process - 1
            for cat1 in all_cats:
                parent_equivalents = set()
                for parent in cat1.parents.all():
                    if category_levels.get(parent.id) == parent_level:
                        # **THE FIX IS HERE: Query both sides of the relationship**
                        equiv_links = CategoryEquivalence.objects.filter(
                            Q(from_category=parent) | Q(to_category=parent)
                        ).select_related('from_category', 'to_category')
                        
                        for link in equiv_links:
                            if link.from_category_id == parent.id:
                                parent_equivalents.add(link.to_category)
                            else:
                                parent_equivalents.add(link.from_category)
                
                for equiv_parent in parent_equivalents:
                    for cat2 in equiv_parent.subcategories.filter(id__in=categories_at_level):
                        if cat1.company_id != cat2.company_id:
                            potential_pairs.append((cat1, cat2))

        # --- Scoring and Filtering (same for all levels) ---
        scored_pairs = []
        unique_pairs = set()
        for cat1, cat2 in potential_pairs:
            pair_key = tuple(sorted((cat1.id, cat2.id)))
            if pair_key in unique_pairs: continue
            unique_pairs.add(pair_key)

            set1, set2 = product_sets.get(cat1.id, set()), product_sets.get(cat2.id, set())
            if not set1 or not set2: continue
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            score = len(intersection) / len(union) if union else 0
            if score > 0.01:
                scored_pairs.append({
                    'cat1': cat1, 'cat2': cat2, 'score': score, 'shared_products': intersection
                })
        scored_pairs.sort(key=lambda x: x['score'], reverse=True)

        # --- Filtering and Interactive Loop (same as before) ---
        processed_db_pairs = set()
        for eq in CategoryEquivalence.objects.all(): processed_db_pairs.add(tuple(sorted((eq.from_category_id, eq.to_category_id))))
        non_matches = load_non_matches()
        skipped_pairs = load_skipped()
        pairs_to_review = [p for p in scored_pairs if tuple(sorted((p['cat1'].id, p['cat2'].id))) not in processed_db_pairs and tuple(sorted((p['cat1'].id, p['cat2'].id))) not in non_matches and tuple(sorted((p['cat1'].id, p['cat2'].id))) not in skipped_pairs]

        if not pairs_to_review: self.stdout.write(self.style.SUCCESS("No new category pairs to review.")); return

        decisions = []
        for i, pair_data in enumerate(pairs_to_review):
            os.system('cls' if os.name == 'nt' else 'clear')
            cat1, cat2, score = pair_data['cat1'], pair_data['cat2'], pair_data['score']
            self.stdout.write(self.style.SUCCESS(f"--- Pair {i + 1} of {len(pairs_to_review)} [LEVEL {level_to_process}] ---"))
            self.stdout.write(f"A: {self.style.SQL_FIELD(cat1.name)} ({cat1.company.name})\nB: {self.style.SQL_FIELD(cat2.name)} ({cat2.company.name})")
            self.stdout.write(f"Similarity Score: {self.style.HTTP_INFO(f'{score:.2f}')}")
            self.stdout.write("Shared Products:")
            shared_product_ids = pair_data['shared_products']
            from products.models import Product
            shared_products = Product.objects.filter(id__in=list(shared_product_ids)[:5])
            for p in shared_products: self.stdout.write(f"  - {p.name}")
            if len(shared_product_ids) > 5: self.stdout.write(f"  ...and {len(shared_product_ids) - 5} more.")
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
                if choice in ['1', '2', '3', '4', '5', 'q']: break
                self.stdout.write(self.style.ERROR("Invalid input."))
            if choice == 'q': break
            if choice == '4': append_skipped(cat1.id, cat2.id); self.stdout.write(self.style.SUCCESS("Skipped."));
            elif choice == '5': append_non_match(cat1.id, cat2.id); self.stdout.write(self.style.SUCCESS("Marked as not a match."));
            elif choice == '1': decisions.append({'from': cat1.id, 'to': cat2.id, 'type': 'SUB'}); self.stdout.write(self.style.SUCCESS("Decision recorded."));
            elif choice == '2': decisions.append({'from': cat2.id, 'to': cat1.id, 'type': 'SUB'}); self.stdout.write(self.style.SUCCESS("Decision recorded."));
            elif choice == '3': decisions.append({'from': cat1.id, 'to': cat2.id, 'type': 'EQ'}); decisions.append({'from': cat2.id, 'to': cat1.id, 'type': 'EQ'}); self.stdout.write(self.style.SUCCESS("Decision recorded."));
            time.sleep(0.75)

        if decisions:
            inbox_dir = 'api/data/category_link_inbox'
            if not os.path.exists(inbox_dir): os.makedirs(inbox_dir)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(inbox_dir, f"{timestamp}.json")
            with open(filename, 'w') as f: json.dump(decisions, f, indent=4)
            self.stdout.write(self.style.SUCCESS(f"\nSession finished. {len(decisions)} decisions saved to {filename}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nSession finished. No new decisions were made."))
