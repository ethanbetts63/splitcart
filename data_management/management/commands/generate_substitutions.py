
import re
import json
import os
import unicodedata
from itertools import combinations
from collections import defaultdict

import requests
from django.core.management.base import BaseCommand
from django.conf import settings

# --- Helper Classes (Adapted from project utils) ---

# NOTE: The following classes are adapted from the project's utils.
# They are included here to make this command a self-contained script
# for local execution, without needing the full Django project context beyond settings.

# Mock translation tables. In a future version, these could be fetched from an API.
BRAND_NAME_TRANSLATIONS = {}
PRODUCT_NAME_TRANSLATIONS = {}

class LocalProductNormalizer:
    def __init__(self, product_data, brand_cache=None):
        self.name = str(product_data.get('name', ''))
        self.brand = str(product_data.get('brand')) if product_data.get('brand') else ''
        self.size = str(product_data.get('size', ''))
        self.raw_sizes = self._extract_all_sizes()
        self.standardized_sizes = self._get_standardized_sizes()

    def _extract_all_sizes(self) -> list:
        all_sizes = set()
        for text in [self.name, self.brand, self.size]:
            if not text: continue
            sizes = self._extract_sizes_from_string(text)
            for size in sizes:
                all_sizes.add(size.lower())
        return sorted(list(all_sizes))

    def _extract_sizes_from_string(self, text: str) -> list:
        sizes = set()
        # This is a simplified version of the original complex regex for portability.
        # It captures patterns like '500g', '1.5l', '6pk'.
        pattern = r'(\d+\.?\d*)\s*(g|kg|ml|l|pk|pack|each|ea)\b'
        for match in re.finditer(pattern, text.lower()):
            value, unit = match.groups()
            unit = unit.replace('pack', 'pk').replace('each', 'ea')
            sizes.add(f"{value}{unit}")
        return list(sizes)

    def _get_standardized_sizes(self) -> list:
        size_comparer = LocalSizeComparer()
        canonical_sizes = {}
        for size_str in self.raw_sizes:
            s = size_str.lower().replace(" ", "").replace("pack", "pk").replace("each", "ea")
            if s == '1ea': s = 'ea'
            parsed_tuple = size_comparer._parse_size(s)
            if parsed_tuple:
                if parsed_tuple not in canonical_sizes:
                    value, unit = parsed_tuple
                    canonical_sizes[parsed_tuple] = f"{int(value) if value.is_integer() else value}{unit}"
            else:
                if s not in canonical_sizes.values():
                    canonical_sizes[('str', s)] = s
        return sorted(list(canonical_sizes.values()))

class LocalSizeComparer:
    def __init__(self):
        self.conversion_map = {
            'g':  {'base': 'g',  'multiplier': 1.0},
            'kg': {'base': 'g',  'multiplier': 1000.0},
            'ml': {'base': 'ml', 'multiplier': 1.0},
            'l':  {'base': 'ml', 'multiplier': 1000.0},
            'pk': {'base': 'pk', 'multiplier': 1.0},
            'ea': {'base': 'ea', 'multiplier': 1.0},
        }
        self.size_pattern = re.compile(r"(\d+\.?\d*)\s*([a-z]+)$")

    def _parse_size(self, size_str: str) -> tuple | None:
        match = self.size_pattern.match(size_str)
        if not match: return None
        value_str, unit_str = match.groups()
        value = float(value_str)
        unit_info = self.conversion_map.get(unit_str)
        if not unit_info: return None
        return (value * unit_info['multiplier'], unit_info['base'])

    def get_canonical_sizes(self, product_dict) -> set:
        normalizer = LocalProductNormalizer(product_dict)
        canonical_sizes = set()
        for size_str in normalizer.standardized_sizes:
            parsed_size = self._parse_size(size_str)
            if parsed_size: canonical_sizes.add(parsed_size)
        return canonical_sizes

    def are_sizes_compatible(self, prod_a, prod_b, tolerance=0.1) -> bool:
        sizes_a = self.get_canonical_sizes(prod_a)
        sizes_b = self.get_canonical_sizes(prod_b)
        if not sizes_a or not sizes_b: return False
        for val_a, unit_a in sizes_a:
            for val_b, unit_b in sizes_b:
                if unit_a == unit_b:
                    if unit_a == 'pk':
                        if val_a == val_b: return True
                    else:
                        if abs(val_a - val_b) <= (val_a * tolerance): return True
        return False

# --- Local Substitution Generators ---

class LocalLvl1SubGenerator:
    def generate(self, command, products):
        command.stdout.write("--- Generating Level 1 Subs ---")
        subs = []
        size_comparer = LocalSizeComparer()
        
        # Group products by brand and normalized name
        name_map = defaultdict(list)
        for p in products:
            if p.get('brand_id') and p.get('normalized_name'):
                key = (p['brand_id'], p['normalized_name'])
                name_map[key].append(p)

        for product_group in name_map.values():
            if len(product_group) > 1:
                for prod_a, prod_b in combinations(product_group, 2):
                    sizes_a = size_comparer.get_canonical_sizes(prod_a)
                    sizes_b = size_comparer.get_canonical_sizes(prod_b)
                    if sizes_a and sizes_b and sizes_a != sizes_b:
                        subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL1', 'score': 1.0, 'source': 'local_strict_name_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl1 subs.")
        return subs

class LocalLvl2SubGenerator:
    def generate(self, command, products):
        command.stdout.write("--- Generating Level 2 Subs ---")
        try: from thefuzz import fuzz
        except ImportError: command.stderr.write("Lvl2 requires 'thefuzz'. Please pip install it."); return []
        
        subs = []
        size_comparer = LocalSizeComparer()
        products_by_brand = defaultdict(list)
        for p in products: 
            if p.get('brand_id'): products_by_brand[p['brand_id']].append(p)

        for brand_id, product_list in products_by_brand.items():
            if len(product_list) < 2: continue
            
            groups = []
            for p in product_list:
                if not p.get('normalized_name'): continue
                placed = False
                for group in groups:
                    rep = group[0]
                    score = fuzz.token_set_ratio(p['normalized_name'], rep['normalized_name'])
                    if 90 < score < 100:
                        group.append(p); placed = True; break
                if not placed: groups.append([p])

            for group in groups:
                if len(group) > 1:
                    for prod_a, prod_b in combinations(group, 2):
                        if size_comparer.are_sizes_compatible(prod_a, prod_b):
                            subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL2', 'score': 0.95, 'source': 'local_size_similarity_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl2 subs.")
        return subs

class LocalLvl3SubGenerator:
    def generate(self, command, products, categories):
        command.stdout.write("--- Generating Level 3 Subs ---")
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError: command.stderr.write("Lvl3 requires 'torch' and 'sentence-transformers'."); return []

        subs = []
        model = SentenceTransformer('all-MiniLM-L6-v2')
        products_by_cat = defaultdict(list)
        for p in products: 
            for cat_id in p.get('category', []): products_by_cat[cat_id].append(p)

        for cat in categories:
            products_in_cat = products_by_cat.get(cat['id'], [])
            if len(products_in_cat) < 2: continue

            corpus = [p['normalized_name'] for p in products_in_cat]
            corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
            cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)
            indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

            for r, c in zip(indices_rows, indices_cols):
                if r.item() >= c.item(): continue
                prod_a = products_in_cat[r.item()]
                prod_b = products_in_cat[c.item()]
                subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL3', 'score': cosine_scores[r,c].item(), 'source': 'local_sbert_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl3 subs.")
        return subs

class LocalLvl4SubGenerator:
    def generate(self, command, products, category_links):
        command.stdout.write("--- Generating Level 4 Subs ---")
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError: command.stderr.write("Lvl4 requires 'torch' and 'sentence-transformers'."); return []

        subs = []
        model = SentenceTransformer('all-MiniLM-L6-v2')
        graph = defaultdict(set)
        all_cat_ids = set()
        for link in category_links:
            graph[link['category_a_id']].add(link['category_b_id'])
            graph[link['category_b_id']].add(link['category_a_id'])
            all_cat_ids.update([link['category_a_id'], link['category_b_id']])

        visited, super_groups = set(), []
        for cat_id in all_cat_ids:
            if cat_id not in visited:
                current_group, stack = set(), [cat_id]
                while stack:
                    node = stack.pop()
                    if node not in visited: visited.add(node); current_group.add(node); stack.extend(graph[node] - visited)
                super_groups.append(current_group)

        products_by_cat = defaultdict(list)
        for p in products: 
            for cat_id in p.get('category', []): products_by_cat[cat_id].append(p)

        for group_ids in super_groups:
            products_in_group = [p for cat_id in group_ids for p in products_by_cat.get(cat_id, [])]
            if len(products_in_group) < 2: continue

            corpus = [p['normalized_name'] for p in products_in_group]
            corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
            cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)
            indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

            for r, c in zip(indices_rows, indices_cols):
                if r.item() >= c.item(): continue
                prod_a = products_in_group[r.item()]
                prod_b = products_in_group[c.item()]
                if set(prod_a.get('category', [])).intersection(set(prod_b.get('category', []))): continue
                subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL4', 'score': cosine_scores[r,c].item(), 'source': 'local_sbert_linked_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl4 subs.")
        return subs

# --- Main Command ---

class Command(BaseCommand):
    help = 'Generates product substitutions locally and saves them to an outbox.'

    def handle(self, *args, **options):
        try:
            server_url = settings.API_SERVER_URL
            api_key = settings.API_SECRET_KEY
        except AttributeError:
            self.stderr.write("API_SERVER_URL and API_SECRET_KEY must be set in settings.")
            return

        headers = {'X-API-KEY': api_key, 'Accept': 'application/json'}
        self.stdout.write(f"--- Starting Substitution Generation using API at {server_url} ---")

        # 1. Fetch all necessary data
        try:
            self.stdout.write("Fetching products...")
            products = requests.get(f"{server_url}/api/export/products/", headers=headers).json()
            self.stdout.write(f"Fetched {len(products)} products.")

            self.stdout.write("Fetching categories...")
            categories = requests.get(f"{server_url}/api/export/categories/", headers=headers).json()
            self.stdout.write(f"Fetched {len(categories)} categories.")

            self.stdout.write("Fetching category links...")
            category_links = requests.get(f"{server_url}/api/export/category_links/", headers=headers).json()
            self.stdout.write(f"Fetched {len(category_links)} category links.")

        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Failed to fetch data: {e}"); return
        except json.JSONDecodeError as e:
            self.stderr.write(f"Failed to decode JSON: {e}"); return

        # 2. Run all generators
        lvl1_subs = LocalLvl1SubGenerator().generate(self, products)
        lvl2_subs = LocalLvl2SubGenerator().generate(self, products)
        lvl3_subs = LocalLvl3SubGenerator().generate(self, products, categories)
        lvl4_subs = LocalLvl4SubGenerator().generate(self, products, category_links)

        all_subs = lvl1_subs + lvl2_subs + lvl3_subs + lvl4_subs
        self.stdout.write(self.style.SUCCESS(f"Total substitutions generated: {len(all_subs)}"))

        # 3. Save to outbox
        outbox_dir = 'data_management/data/substitutions_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'substitutions.json')
        with open(output_path, 'w') as f:
            json.dump(all_subs, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS(f"Saved {len(all_subs)} substitutions to {output_path}"))
        self.stdout.write(self.style.SUCCESS("--- Substitution Generation Finished ---"))
