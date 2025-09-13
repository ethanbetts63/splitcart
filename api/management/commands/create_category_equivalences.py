import os
import msvcrt
import json
from itertools import combinations
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, CategoryEquivalence

# Helper functions for managing non-matches
NON_MATCH_FILE = 'api/data/analysis/category_non_matches.json'

def load_non_matches():
    if not os.path.exists(NON_MATCH_FILE):
        return set()
    with open(NON_MATCH_FILE, 'r') as f:
        pairs = json.load(f)
        return set(tuple(sorted(p)) for p in pairs)

def append_non_match(cat1_id, cat2_id):
    if not os.path.exists(os.path.dirname(NON_MATCH_FILE)):
        os.makedirs(os.path.dirname(NON_MATCH_FILE))
    non_matches_set = load_non_matches()
    non_matches_list = [list(p) for p in non_matches_set]
    pair = sorted([cat1_id, cat2_id])
    if pair not in non_matches_list:
        non_matches_list.append(pair)
        with open(NON_MATCH_FILE, 'w') as f:
            json.dump(non_matches_list, f, indent=4)

class Command(BaseCommand):
    help = 'Interactively create equivalence rules for Level 0 categories.'

    def handle(self, *args, **options):
        # 1. Get potential pairs using Jaccard similarity
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
                    if score > 0.05: # Low threshold to get more suggestions
                        potential_pairs.append({
                            'cat1': cat1, 'cat2': cat2, 'score': score, 'shared_products': intersection
                        })
        
        # Sort by score, highest first
        potential_pairs.sort(key=lambda x: x['score'], reverse=True)

        # 2. Filter out already processed pairs
        processed_pairs = set()
        for eq in CategoryEquivalence.objects.all():
            processed_pairs.add(tuple(sorted((eq.from_category_id, eq.to_category_id))))
        
        non_matches = load_non_matches()
        pairs_to_review = [
            p for p in potential_pairs 
            if tuple(sorted((p['cat1'].id, p['cat2'].id))) not in processed_pairs 
            and tuple(sorted((p['cat1'].id, p['cat2'].id))) not in non_matches
        ]

        if not pairs_to_review:
            self.stdout.write(self.style.SUCCESS("No new category pairs to review."))
            return

        # 3. The Interactive Loop
        for i, pair_data in enumerate(pairs_to_review):
            os.system('cls' if os.name == 'nt' else 'clear')
            cat1, cat2, score = pair_data['cat1'], pair_data['cat2'], pair_data['score']

            self.stdout.write(self.style.SUCCESS(f"--- Pair {i + 1} of {len(pairs_to_review)} ---"))
            self.stdout.write(f"A: {self.style.SQL_FIELD(cat1.name)} ({cat1.company.name})\nB: {self.style.SQL_FIELD(cat2.name)} ({cat2.company.name})")
            self.stdout.write(f"Similarity Score: {self.style.HTTP_INFO(f'{score:.2f}')}")
            self.stdout.write("-" * 50)
            self.stdout.write("Shared Products:")
            shared_product_ids = pair_data['shared_products']
            # To get product names, we need another query. Let's just show IDs for now for speed.
            # In a real implementation, fetching names would be better.
            from products.models import Product
            shared_products = Product.objects.filter(id__in=list(shared_product_ids)[:5])
            for p in shared_products:
                self.stdout.write(f"  - {p.name}")
            if len(shared_product_ids) > 5:
                self.stdout.write(f"  ...and {len(shared_product_ids) - 5} more.")
            self.stdout.write("-" * 50)

            self.stdout.write(f"  {self.style.SQL_KEYWORD('[1]')} '{cat1.name}' is SUBSET of '{cat2.name}'")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[2]')} '{cat2.name}' is SUBSET of '{cat1.name}'")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[3]')} Mutually EQUIVALENT")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[4]')} NOT a match")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[s]')} Skip")
            self.stdout.write(f"  {self.style.SQL_KEYWORD('[q]')} Quit")

            while True:
                self.stdout.write(self.style.HTTP_REDIRECT("\nChoose an option: "), ending="")
                self.stdout.flush()
                choice = msvcrt.getch().decode('utf-8').lower()
                self.stdout.write(choice + '\n')
                if choice in ['1', '2', '3', '4', 's', 'q']:
                    break
                self.stdout.write(self.style.ERROR("Invalid input."))

            if choice == 'q': break
            if choice == 's': continue

            if choice == '1':
                CategoryEquivalence.objects.create(from_category=cat1, to_category=cat2, relationship_type='SUB')
                self.stdout.write(self.style.SUCCESS(f"Saved: {cat1.name} -> {cat2.name}"))
            elif choice == '2':
                CategoryEquivalence.objects.create(from_category=cat2, to_category=cat1, relationship_type='SUB')
                self.stdout.write(self.style.SUCCESS(f"Saved: {cat2.name} -> {cat1.name}"))
            elif choice == '3':
                # For mutual equivalence, create two records to make querying easier
                CategoryEquivalence.objects.create(from_category=cat1, to_category=cat2, relationship_type='EQ')
                CategoryEquivalence.objects.create(from_category=cat2, to_category=cat1, relationship_type='EQ')
                self.stdout.write(self.style.SUCCESS(f"Saved: {cat1.name} <=> {cat2.name}"))
            elif choice == '4':
                append_non_match(cat1.id, cat2.id)
                self.stdout.write(self.style.SUCCESS("Marked as not a match."))
            
            # Pause to see the result
            msvcrt.getch()

        self.stdout.write(self.style.SUCCESS("\nCategory equivalence session finished."))