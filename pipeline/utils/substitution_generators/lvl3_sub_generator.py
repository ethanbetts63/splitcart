from collections import defaultdict
import torch


class Lvl3SubGenerator:
    def __init__(self, command):
        self.command = command
        self.model = self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.command.stdout.write("  - Loading sentence transformer model (all-MiniLM-L6-v2)...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            self.command.stdout.write(self.command.style.SUCCESS("  - Model loaded successfully."))
            return model
        except ImportError:
            self.command.stderr.write("Lvl3 requires 'torch' and 'sentence-transformers'. Please install them.")
            return None

    def generate(self, products):
        """
        Generates Level 3 substitutions using sentence similarity.

        Groups products by primary_category_slug (cross-company). Products sharing
        a slug are compared by name embedding cosine similarity.
        """
        if not self.model:
            return []

        from sentence_transformers import util
        self.command.stdout.write("--- Generating Level 3 Subs ---")

        # Group products by each primary_category_slug they carry
        products_by_slug = defaultdict(list)
        for p in products:
            for slug in p.get('primary_category_slugs') or []:
                products_by_slug[slug].append(p)

        if not products_by_slug:
            self.command.stdout.write("  - No products with primary_category_slugs found.")
            return []

        # Encode all unique products once
        unique_products = {p['id']: p for slug_products in products_by_slug.values() for p in slug_products}
        product_list = list(unique_products.values())
        corpus_names = [p['name'] for p in product_list]

        self.command.stdout.write(f"  - Encoding {len(corpus_names)} product names...")
        corpus_embeddings = self.model.encode(corpus_names, convert_to_tensor=True)
        embedding_map = {product_list[i]['id']: corpus_embeddings[i] for i in range(len(product_list))}

        subs = []
        total_slugs = len(products_by_slug)
        self.command.stdout.write(f"  - Comparing products across {total_slugs} primary category slugs...")

        for i, (slug, products_in_cat) in enumerate(products_by_slug.items()):
            progress_msg = f"  - Processing slug {i + 1}/{total_slugs}: {slug}"
            self.command.stdout.write(progress_msg, ending='\r')

            if len(products_in_cat) < 2:
                continue

            cat_embeddings = [embedding_map[p['id']] for p in products_in_cat if p['id'] in embedding_map]
            if len(cat_embeddings) < 2:
                continue

            cat_corpus_tensor = torch.stack(cat_embeddings)
            cosine_scores = util.cos_sim(cat_corpus_tensor, cat_corpus_tensor)
            indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

            for r, c in zip(indices_rows, indices_cols):
                if r.item() >= c.item():
                    continue
                prod_a = products_in_cat[r.item()]
                prod_b = products_in_cat[c.item()]
                subs.append({
                    'product_a': prod_a['id'],
                    'product_b': prod_b['id'],
                    'level': 'LVL3',
                    'score': cosine_scores[r, c].item(),
                })

        self.command.stdout.write(" " * (len(progress_msg) + 5), ending='\r')
        self.command.stdout.write(self.command.style.SUCCESS(f"  Generated {len(subs)} Lvl3 subs from {total_slugs} primary categories."))
        return subs
