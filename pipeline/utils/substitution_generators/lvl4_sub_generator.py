from collections import defaultdict
import torch
from django.utils.text import slugify
from pipeline.data.category_mappings import PRIMARY_CATEGORY_HIERARCHY


def _build_slug_super_groups() -> list[frozenset]:
    """
    Build super-groups from PRIMARY_CATEGORY_HIERARCHY.
    Each super-group is a frozenset of primary_category_slugs that are
    related (parent + children). Products in the same super-group but in
    different primary categories are Lvl4 substitution candidates.
    """
    groups = []
    for parent_name, child_names in PRIMARY_CATEGORY_HIERARCHY.items():
        all_slugs = {slugify(parent_name)} | {slugify(n) for n in child_names}
        groups.append(frozenset(all_slugs))
    return groups


_SLUG_SUPER_GROUPS = _build_slug_super_groups()


class Lvl4SubGenerator:
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
            self.command.stderr.write("Lvl4 requires 'torch' and 'sentence-transformers'. Please install them.")
            return None

    def generate(self, products):
        """
        Generates Level 4 substitutions using sentence similarity across related
        primary categories (defined by PRIMARY_CATEGORY_HIERARCHY).

        Replaces the old CategoryLink-based approach.
        """
        if not self.model:
            return []

        from sentence_transformers import util
        self.command.stdout.write("--- Generating Level 4 Subs ---")

        # Group products by primary_category_slug
        products_by_slug = defaultdict(list)
        for p in products:
            for slug in p.get('primary_category_slugs') or []:
                products_by_slug[slug].append(p)

        self.command.stdout.write(f"  - Found {len(_SLUG_SUPER_GROUPS)} category super-groups from hierarchy.")

        # Collect all unique products that appear in any super-group
        products_in_any_group = {}
        for group in _SLUG_SUPER_GROUPS:
            for slug in group:
                for p in products_by_slug.get(slug, []):
                    products_in_any_group[p['id']] = p

        product_list = list(products_in_any_group.values())
        corpus_names = [p['name'] for p in product_list]

        if not corpus_names:
            self.command.stdout.write("  - No products found in related categories to process.")
            return []

        self.command.stdout.write(f"  - Encoding {len(corpus_names)} product names...")
        corpus_embeddings = self.model.encode(corpus_names, convert_to_tensor=True)
        embedding_map = {product_list[i]['id']: corpus_embeddings[i] for i in range(len(product_list))}

        subs = []
        total_groups = len(_SLUG_SUPER_GROUPS)

        for i, group_slugs in enumerate(_SLUG_SUPER_GROUPS):
            progress_msg = f"  - Processing super-groups: {i + 1}/{total_groups}"
            self.command.stdout.write(progress_msg, ending='\r')

            # Collect all products in this super-group, tracking their slug
            products_in_group = []
            product_slug_map = {}  # product_id -> set of slugs in this group
            for slug in group_slugs:
                for p in products_by_slug.get(slug, []):
                    products_in_group.append(p)
                    product_slug_map.setdefault(p['id'], set()).add(slug)

            if len(products_in_group) < 2:
                continue

            group_embeddings = [embedding_map[p['id']] for p in products_in_group if p['id'] in embedding_map]
            if len(group_embeddings) < 2:
                continue

            group_corpus_tensor = torch.stack(group_embeddings)
            cosine_scores = util.cos_sim(group_corpus_tensor, group_corpus_tensor)
            indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

            for r, c in zip(indices_rows, indices_cols):
                if r.item() >= c.item():
                    continue
                prod_a = products_in_group[r.item()]
                prod_b = products_in_group[c.item()]

                # Only Lvl4 if the products are in DIFFERENT primary categories
                # (same primary category is already handled by Lvl3)
                slugs_a = product_slug_map.get(prod_a['id'], set())
                slugs_b = product_slug_map.get(prod_b['id'], set())
                if slugs_a & slugs_b:  # overlap = same primary category
                    continue

                subs.append({
                    'product_a': prod_a['id'],
                    'product_b': prod_b['id'],
                    'level': 'LVL4',
                    'score': cosine_scores[r, c].item(),
                })

        self.command.stdout.write(" " * (len(progress_msg) + 5), ending='\r')
        self.command.stdout.write(self.command.style.SUCCESS(f"  Generated {len(subs)} Lvl4 subs from {total_groups} super-groups."))
        return subs
