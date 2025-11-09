from collections import defaultdict
import torch

class Lvl4SubGenerator:
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
            self.command.stderr.write("Lvl4 requires 'torch' and 'sentence-transformers'. Please install them.")
            return None

    def generate(self, products, category_links):
        """Generates Level 4 substitutions using sentence similarity on linked categories."""
        if not self.model:
            return []

        from sentence_transformers import util
        self.command.stdout.write("--- Generating Level 4 Subs ---")

        # Step 1: Build category graph and find connected "super groups"
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
                    if node not in visited:
                        visited.add(node)
                        current_group.add(node)
                        stack.extend(graph[node] - visited)
                super_groups.append(current_group)
        
        self.command.stdout.write(f"  - Found {len(super_groups)} category super-groups.")

        # Step 2: Group products by category
        products_by_cat = defaultdict(list)
        for p in products:
            for cat_id in p.get('category', []):
                products_by_cat[cat_id].append(p)

        # Step 3: Create a flat list of unique products to be encoded
        products_in_any_group = {p['id']: p for group_ids in super_groups for cat_id in group_ids for p in products_by_cat.get(cat_id, [])}
        product_list = list(products_in_any_group.values())
        corpus_names = [p['name'] for p in product_list]

        if not corpus_names:
            self.command.stdout.write("  - No products found in linked categories to process.")
            return []

        # Step 4: Batch encode all product names
        self.command.stdout.write(f"  - Encoding {len(corpus_names)} product names...")
        corpus_embeddings = self.model.encode(corpus_names, convert_to_tensor=True)
        embedding_map = {product_list[i]['id']: corpus_embeddings[i] for i in range(len(product_list))}

        # Step 5: Process each super-group to find similar pairs
        subs = []
        total_groups = len(super_groups)
        self.command.stdout.write(f"  - Comparing products in {total_groups} super-groups...")

        for i, group_ids in enumerate(super_groups):
            progress_msg = f"  - Processing super-groups: {i + 1}/{total_groups}"
            self.command.stdout.write(progress_msg, ending='\r')

            products_in_group = [p for cat_id in group_ids for p in products_by_cat.get(cat_id, [])]
            if len(products_in_group) < 2:
                continue

            # Gather pre-computed embeddings
            group_embeddings = [embedding_map[p['id']] for p in products_in_group if p['id'] in embedding_map]
            if len(group_embeddings) < 2:
                continue
            
            group_corpus_tensor = torch.stack(group_embeddings)

            # Compute cosine similarity
            cosine_scores = util.cos_sim(group_corpus_tensor, group_corpus_tensor)
            indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

            for r, c in zip(indices_rows, indices_cols):
                if r.item() >= c.item():
                    continue
                
                prod_a = products_in_group[r.item()]
                prod_b = products_in_group[c.item()]

                # Ensure products are not in the same category (that's a Lvl3 sub)
                if not set(prod_a.get('category', [])).isdisjoint(set(prod_b.get('category', []))):
                    continue
                
                subs.append({
                    'product_a': prod_a['id'],
                    'product_b': prod_b['id'],
                    'level': 'LVL4',
                    'score': cosine_scores[r, c].item()
                })

        # Clear the progress line
        self.command.stdout.write(" " * (len(progress_msg) + 5), ending='\r')
        self.command.stdout.write(self.command.style.SUCCESS(f"  Generated {len(subs)} Lvl4 subs from {total_groups} super-groups."))
        return subs
