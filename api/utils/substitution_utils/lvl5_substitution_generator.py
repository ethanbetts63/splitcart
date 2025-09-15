from django.db.models import Count
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product
from companies.models import Category
from sentence_transformers import SentenceTransformer, util
import torch

class Lvl5SubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 5: Semantic Similarity.
    Uses a Sentence Transformer model to find semantically similar products,
    regardless of textual similarity, brand, or size.
    """
    def generate(self):
        level_definition = "Semantic Similarity (Sentence Transformer)"
        self.command.stdout.write(f"--- Generating Level 5: {level_definition} ---")
        
        new_substitutions_count = 0
        # Using a pre-trained model specialized for semantic similarity
        model_name = 'all-MiniLM-L6-v2'
        model = SentenceTransformer(model_name)

        similarity_threshold = 0.75  # Higher threshold for this more powerful model

        # Get all categories that have at least 2 products
        categories = Category.objects.annotate(
            num_products=Count('products')
        ).filter(num_products__gte=2)

        self.command.stdout.write(f"Found {len(categories)} categories with 2 or more products to analyze.")

        for i, category in enumerate(categories):
            self.command.stdout.write(f"-- Processing Category {i+1}/{len(categories)}: '{category.name}' --")
            
            products_in_cat = list(Product.objects.filter(category=category))
            if len(products_in_cat) < 2:
                continue

            # Use the product's normalized_name for semantic encoding
            corpus = [p.normalized_name for p in products_in_cat]
            corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

            # Compute cosine similarity scores
            cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)

            # Use torch.where to find pairs above the threshold
            indices_rows, indices_cols = torch.where(cosine_scores > similarity_threshold)

            for prod_idx_a, prod_idx_b in zip(indices_rows, indices_cols):
                # Convert tensor indices to python integers
                prod_idx_a = prod_idx_a.item()
                prod_idx_b = prod_idx_b.item()

                # Ensure we are not comparing a product to itself and avoid duplicate pairs
                if prod_idx_a >= prod_idx_b:
                    continue

                prod_a = products_in_cat[prod_idx_a]
                prod_b = products_in_cat[prod_idx_b]

                # For Level 5, we are intentionally ignoring brand and size to find novel substitutes
                
                score = cosine_scores[prod_idx_a, prod_idx_b].item()
                _, created = self._create_substitution(
                    prod_a, 
                    prod_b, 
                    level='LVL5',
                    score=score, 
                    source='sbert_v1'
                )
                if created:
                    new_substitutions_count += 1

        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new Level 5 substitutions."))
