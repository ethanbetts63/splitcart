from itertools import combinations
from collections import defaultdict

class Lvl1SubGenerator:
    def generate(self, command, products):
        command.stdout.write("--- Generating Level 1 Subs ---")
        subs = []
        
        # Group products by brand and normalized name
        name_map = defaultdict(list)
        for p in products:
            if p.get('brand_id') and p.get('normalized_name'):
                key = (p['brand_id'], p['normalized_name'])
                name_map[key].append(p)

        for product_group in name_map.values():
            if len(product_group) > 1:
                for prod_a, prod_b in combinations(product_group, 2):
                    sizes_a = set(prod_a.get('sizes', []))
                    sizes_b = set(prod_b.get('sizes', []))
                    if sizes_a and sizes_b and sizes_a != sizes_b:
                        subs.append({'product_a': prod_a['id'], 'product_b': prod_b['id'], 'level': 'LVL1', 'score': 1.0, 'source': 'local_strict_name_v1'})
        command.stdout.write(f"  Generated {len(subs)} Lvl1 subs.")
        return subs
