from collections import defaultdict
import torch

class Lvl3SubGenerator:
    def __init__(self, command):
        self.command = command
        self.model = self._load_model()

    def _load_model(self):
        """Loads the SentenceTransformer model, handling potential import errors."""
        try:
            from sentence_transformers import SentenceTransformer
            self.command.stdout.write("  - Loading sentence transformer model (all-MiniLM-L6-v2)...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            self.command.stdout.write(self.command.style.SUCCESS("  - Model loaded successfully."))
            return model
        except ImportError:
            self.command.stderr.write("Lvl3 requires 'torch' and 'sentence-transformers'. Please install them.")
            return None

    def generate(self, products, categories):
        """Generates Level 3 substitutions using sentence similarity."""
        if not self.model:
            return []
            
        from sentence_transformers import util
        self.command.stdout.write("--- Generating Level 3 Subs ---")

        # Step 1: Group products by category
        products_by_cat = defaultdict(list)
        for p in products:
            for cat_id in p.get('category', []):
                products_by_cat[cat_id].append(p)

        # Step 2: Create a flat list of unique products to be encoded
        unique_products = {p['id']: p for cat_id in products_by_cat for p in products_by_cat[cat_id]}
        product_list = list(unique_products.values())
        product_map = {p['id']: p for p in product_list}
        corpus_names = [p['name'] for p in product_list]

        if not corpus_names:
            self.command.stdout.write("  - No products found to process.")
            return []

        # Step 3: Batch encode all product names at once for efficiency
        self.command.stdout.write(f"  - Encoding {len(corpus_names)} product names...")
        corpus_embeddings = self.model.encode(corpus_names, convert_to_tensor=True, show_progress_bar=True)
        
        # Create a mapping from product ID to its embedding
        embedding_map = {product_list[i]['id']: corpus_embeddings[i] for i in range(len(product_list))}

        # Step 4: Process each category to find similar pairs
        subs = []
        total_cats = len(categories)
        self.command.stdout.write(f"  - Comparing products in {total_cats} categories...")

        for i, cat in enumerate(categories):
            progress_msg = f"  - Processing categories: {i + 1}/{total_cats}"
            self.command.stdout.write(progress_msg, ending='\r')

            products_in_cat = products_by_cat.get(cat['id'], [])
            if len(products_in_cat) < 2:
                continue

            # Gather the pre-computed embeddings for this category
            cat_embeddings = [embedding_map[p['id']] for p in products_in_cat if p['id'] in embedding_map]
            if len(cat_embeddings) < 2:
                continue
            
            cat_corpus_tensor = torch.stack(cat_embeddings)

            # Compute cosine similarity for the current category
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
                    'source': 'local_sbert_v1'
                })
        
        # Clear the progress line
        self.command.stdout.write(" " * (len(progress_msg) + 5), ending='\r')
        self.command.stdout.write(self.command.style.SUCCESS(f"  Generated {len(subs)} Lvl3 subs from {total_cats} categories."))
        return subs
