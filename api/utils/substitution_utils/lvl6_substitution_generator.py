from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product
from companies.models import CategoryLink
from sentence_transformers import SentenceTransformer, util
import torch
from collections import defaultdict

class Lvl6SubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 6: Linked Category Semantic Similarity.
    Uses CategoryLink to group related categories across companies and then
    applies Sentence Transformer to find semantically similar products within these groups.
    """
    def generate(self):
        level_definition = "Linked Category Semantic Similarity (Sentence Transformer)"
        self.command.stdout.write(f"--- Generating Level 6: {level_definition} ---")
        
        new_substitutions_count = 0
        model_name = 'all-MiniLM-L6-v2'
        model = SentenceTransformer(model_name)

        similarity_threshold = 0.75  # Can be adjusted

        # 1. Build graph of linked categories
        self.command.stdout.write("Building graph of linked categories...")
        graph = defaultdict(set)
        all_category_ids = set()

        # Consider all linked types for this consolidated level
        for link in CategoryLink.objects.filter(link_type__in=['MATCH', 'CLOSE', 'DISTANT']):
            graph[link.category_a_id].add(link.category_b_id)
            graph[link.category_b_id].add(link.category_a_id)
            all_category_ids.add(link.category_a_id)
            all_category_ids.add(link.category_b_id)

        if not all_category_ids:
            self.command.stdout.write("No category links found. Skipping Level 6 generation.")
            return

        # 2. Find connected components (super-groups of linked categories)
        self.command.stdout.write("Finding connected components of categories...")
        visited = set()
        super_groups = []

        for cat_id in all_category_ids:
            if cat_id not in visited:
                current_group = set()
                stack = [cat_id]
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        current_group.add(node)
                        stack.extend(graph[node] - visited)
                super_groups.append(current_group)
        
        self.command.stdout.write(f"Found {len(super_groups)} super-groups of linked categories.")

        # 3. Process each super-group
        for i, group_ids in enumerate(super_groups):
            self.command.stdout.write(f"-- Processing Super-Group {i+1}/{len(super_groups)} (containing {len(group_ids)} categories) --")
            
            # Fetch all products from all categories in this super-group
            products_in_group = list(Product.objects.filter(category__id__in=list(group_ids)))
            
            if len(products_in_group) < 2:
                self.command.stdout.write("  (Less than 2 products in group, skipping semantic analysis)")
                continue

            corpus = [p.normalized_name for p in products_in_group]
            corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

            cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)

            indices_rows, indices_cols = torch.where(cosine_scores > similarity_threshold)

            for prod_idx_a, prod_idx_b in zip(indices_rows, indices_cols):
                prod_idx_a = prod_idx_a.item()
                prod_idx_b = prod_idx_b.item()

                if prod_idx_a >= prod_idx_b:
                    continue

                prod_a = products_in_group[prod_idx_a]
                prod_b = products_in_group[prod_idx_b]

                # Ensure we don't create substitutions for products that share a category,
                # as that is the responsibility of the LVL5 generator.
                prod_a_cats = set(prod_a.category.values_list('id', flat=True))
                prod_b_cats = set(prod_b.category.values_list('id', flat=True))
                if prod_a_cats.intersection(prod_b_cats):
                    continue
                
                score = cosine_scores[prod_idx_a, prod_idx_b].item()
                _, created = self._create_substitution(
                    prod_a, 
                    prod_b, 
                    level='LVL6',
                    score=score, 
                    source='sbert_linked_cat_v1'
                )
                if created:
                    new_substitutions_count += 1

        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new Level 6 substitutions."))
