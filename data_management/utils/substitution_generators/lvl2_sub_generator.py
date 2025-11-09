from itertools import combinations
from collections import defaultdict
from thefuzz import fuzz

class Lvl2SubGenerator:
    def generate(self, command, products):
        command.stdout.write("--- Generating Level 2 Subs ---")
        subs = []
        products_by_brand = defaultdict(list)
        for p in products:
            if p.get('brand_id'):
                products_by_brand[p['brand_id']].append(p)

        brand_items = list(products_by_brand.items())
        total_brands = len(brand_items)
        command.stdout.write(f"  - Analyzing {total_brands} brands for name/size similarities...")

        for i, (brand_id, product_list) in enumerate(brand_items):
            if len(product_list) < 2:
                continue

            progress_msg = f"  - Processing brand {i + 1}/{total_brands}"
            command.stdout.write(progress_msg, ending='\r')

            # Optimization: Use a blocking strategy to reduce comparisons
            blocks = defaultdict(list)
            for p in product_list:
                p_name = p.get('name', '').lower().strip()
                if not p_name:
                    continue
                # Use the first word as a simple block key
                block_key = p_name.split(' ')[0]
                blocks[block_key].append(p)

            # Now, find name-based groups within each smaller block
            final_groups = []
            for block_key, block_products in blocks.items():
                if len(block_products) < 2:
                    final_groups.extend([[p] for p in block_products])
                    continue

                # This is the original grouping logic, but applied to a much smaller list
                groups_in_block = []
                for p in block_products:
                    p_name = p.get('name', '').lower().strip()
                    placed = False
                    for group in groups_in_block:
                        rep = group[0]
                        rep_name = rep.get('name', '').lower().strip()
                        score = fuzz.token_set_ratio(p_name, rep_name)
                        if 90 < score < 100:
                            group.append(p)
                            placed = True
                            break
                    if not placed:
                        groups_in_block.append([p])
                final_groups.extend(groups_in_block)

            # Generate substitutions from the final groups
            for group in final_groups:
                if len(group) > 1:
                    for prod_a, prod_b in combinations(group, 2):
                        # Ensure sizes are identical and not empty
                        sizes_a = set(s for s in prod_a.get('sizes', []) if s)
                        sizes_b = set(s for s in prod_b.get('sizes', []) if s)
                        if sizes_a and sizes_a == sizes_b:
                            subs.append({
                                'product_a': prod_a['id'],
                                'product_b': prod_b['id'],
                                'level': 'LVL2',
                                'score': 0.95
                            })
        
        # Clear the progress line
        command.stdout.write(" " * (len(progress_msg) + 5), ending='\r')
        command.stdout.write(f"  Generated {len(subs)} Lvl2 subs from {total_brands} brands.")
        return subs
