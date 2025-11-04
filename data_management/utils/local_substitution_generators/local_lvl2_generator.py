from itertools import combinations
from collections import defaultdict
from .local_size_comparer import LocalSizeComparer

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
                p_name = p.get('name', '').lower().strip()
                if not p_name: continue

                placed = False
                for group in groups:
                    rep = group[0]
                    rep_name = rep.get('name', '').lower().strip()
                    score = fuzz.token_set_ratio(p_name, rep_name)
                    if 90 < score < 100:
                        group.append(p)
                        placed = True
                        break
                if not placed:
                    groups.append([p])

            for group in groups:
                if len(group) > 1:
                    for prod_a, prod_b in combinations(group, 2):
                        if size_comparer.are_sizes_compatible(prod_a, prod_b):
                            subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL2', 'score': 0.95, 'source': 'local_size_similarity_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl2 subs.")
        return subs
