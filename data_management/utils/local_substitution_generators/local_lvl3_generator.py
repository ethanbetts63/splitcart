from collections import defaultdict

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
