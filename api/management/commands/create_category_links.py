import os
import msvcrt
import json
import time
import datetime
from itertools import combinations
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, CategoryLink

# --- Persistence Helper Functions ---
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
    help = 'Interactively create equivalence rules for categories.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level', type=int, required=False,
            help='The category nesting level to process. Required if not using suggestions.'
        )
        parser.add_argument(
            '--use-suggestions', action='store_true',
            help='Use the pre-generated suggestions file instead of level-based matching.'
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
        use_suggestions = options['use_suggestions']

        if not use_suggestions and level_to_process is None:
            self.stdout.write(self.style.ERROR("You must specify either --level or --use-suggestions."))
            return

        scored_pairs = []

        if use_suggestions:
            self.stdout.write(self.style.SUCCESS("--- Loading suggestions from file ---"))
            try:
                with open('api/data/suggested_category_links.json', 'r') as f:
                    suggestions = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.stdout.write(self.style.ERROR("Could not load or parse suggestion file. Please run `suggest_category_links` first."))
                return
            
            cat_ids = set()
            for s in suggestions:
                cat_ids.add(s['cat1_id'])
                cat_ids.add(s['cat2_id'])
            
            cats_by_id = {cat.id: cat for cat in Category.objects.filter(id__in=cat_ids).prefetch_related('company')}

            for s in suggestions:
                cat1 = cats_by_id.get(s['cat1_id'])
                cat2 = cats_by_id.get(s['cat2_id'])
                if not cat1 or not cat2: continue

                scored_pairs.append({
                    'cat1': cat1, 
                    'cat2': cat2, 
                    'score': s['score'], 
                    'shared_products': set(range(s['shared_products']))
                })

        else: # Original level-based logic
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
                            equiv_links = CategoryLink.objects.filter(
                                Q(category_a=parent) | Q(category_b=parent)
                            ).select_related('category_a', 'category_b')
                            
                            for link in equiv_links:
                                if link.category_a_id == parent.id:
                                    parent_equivalents.add(link.category_b)
                                else:
                                    parent_equivalents.add(link.category_a)
                    
                    for equiv_parent in parent_equivalents:
                        for cat2 in equiv_parent.subcategories.filter(id__in=categories_at_level):
                            if cat1.company_id != cat2.company_id:
                                potential_pairs.append((cat1, cat2))

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

        # --- Filtering and Interactive Loop ---
        processed_db_pairs = set()
        for link in CategoryLink.objects.all():
            processed_db_pairs.add(tuple(sorted((link.category_a_id, link.category_b_id))))
        
        non_matches = load_non_matches()
        skipped_pairs = load_skipped()
        
        pairs_to_review = [
            p for p in scored_pairs 
            if tuple(sorted((p['cat1'].id, p['cat2'].id))) not in processed_db_pairs and \
               tuple(sorted((p['cat1'].id, p['cat2'].id))) not in non_matches and \
               tuple(sorted((p['cat1'].id, p['cat2'].id))) not in skipped_pairs
        ]

        if not pairs_to_review: self.stdout.write(self.style.SUCCESS("No new category pairs to review.")); return

        decisions = []
        for i, pair_data in enumerate(pairs_to_review):
            os.system('cls' if os.name == 'nt' else 'clear')
            cat1, cat2, score = pair_data['cat1'], pair_data['cat2'], pair_data['score']
            
            review_title = f"LEVEL {level_to_process}" if not use_suggestions else "SUGGESTIONS"
            self.stdout.write(self.style.SUCCESS(f"--- Pair {i + 1} of {len(pairs_to_review)} [{review_title}] ---"))

            self.stdout.write(f"A: {self.style.SQL_FIELD(cat1.name)} ({cat1.company.name})\nA: {self.style.SQL_FIELD(cat2.name)} ({cat2.company.name})")
            self.stdout.write(f"Similarity Score: {self.style.HTTP_INFO(f'{score:.2f}')}")
            self.stdout.write("Shared Products:")
            shared_product_ids = pair_data['shared_products']
            from products.models import Product
            try:
                shared_products = Product.objects.filter(id__in=list(shared_product_ids)[:5])
                for p in shared_products: self.stdout.write(f"  - {p.name}")
                if len(shared_product_ids) > 5: self.stdout.write(f"  ...and {len(shared_product_ids) - 5} more.")
            except (TypeError, ValueError):
                 self.stdout.write(f"  ({len(shared_product_ids)} shared products)")

            self.stdout.write("-" * 50)
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[1]')} MATCH")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[2]')} CLOSE Relation")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[3]')} DISTANT Relation")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[4]')} Skip for now")
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
            
            cat_a_id, cat_b_id = tuple(sorted((cat1.id, cat2.id)))

            if choice == '4': 
                append_skipped(cat_a_id, cat_b_id)
                self.stdout.write(self.style.SUCCESS("Skipped."))
            elif choice == '5': 
                append_non_match(cat_a_id, cat_b_id)
                self.stdout.write(self.style.SUCCESS("Marked as not a match."))
            elif choice == '1': 
                decisions.append({'category_a_id': cat_a_id, 'category_b_id': cat_b_id, 'type': 'MATCH'})
                self.stdout.write(self.style.SUCCESS("Decision recorded: MATCH."))
            elif choice == '2': 
                decisions.append({'category_a_id': cat_a_id, 'category_b_id': cat_b_id, 'type': 'CLOSE'})
                self.stdout.write(self.style.SUCCESS("Decision recorded: CLOSE Relation."))
            elif choice == '3': 
                decisions.append({'category_a_id': cat_a_id, 'category_b_id': cat_b_id, 'type': 'DISTANT'})
                self.stdout.write(self.style.SUCCESS("Decision recorded: DISTANT Relation."))
            
        if decisions:
            inbox_dir = 'api/data/category_link_inbox'
            if not os.path.exists(inbox_dir): os.makedirs(inbox_dir)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(inbox_dir, f"{timestamp}.json")
            with open(filename, 'w') as f: json.dump(decisions, f, indent=4)
            self.stdout.write(self.style.SUCCESS(f"\nSession finished. {len(decisions)} decisions saved to {filename}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nSession finished. No new decisions were made."))