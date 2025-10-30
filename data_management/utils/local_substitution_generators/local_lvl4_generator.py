from collections import defaultdict

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
