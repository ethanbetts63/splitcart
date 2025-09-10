from django.db.models import Count
from itertools import combinations
from collections import defaultdict
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product
from companies.models import Category
from .size_comparer import SizeComparer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Lvl3SubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 3: Different brand, similar product, similar size.
    Uses TF-IDF and cosine similarity to find textually similar product names.
    """
    def generate(self):
        level_definition = "Different brand, similar product, similar size."
        self.command.stdout.write(f"--- Generating Level 3: {level_definition} ---")
        
        new_substitutions_count = 0
        size_comparer = SizeComparer()
        similarity_threshold = 0.8  # Similarity score threshold

        # Get all categories that have products from at least two different brands
        categories = Category.objects.annotate(
            num_brands=Count('products__brand', distinct=True)
        ).filter(num_brands__gte=2)

        self.command.stdout.write(f"Found {len(categories)} categories with products from multiple brands to analyze.")

        for i, category in enumerate(categories):
            
            products_in_cat = list(Product.objects.filter(category=category))
            if len(products_in_cat) < 2:
                continue

            # Use normalized_name for TF-IDF
            corpus = [p.normalized_name for p in products_in_cat]
            vectorizer = TfidfVectorizer(stop_words='english', min_df=1, ngram_range=(1, 2))
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
            except ValueError:
                self.command.stdout.write(self.command.style.WARNING(f"Could not generate TF-IDF matrix for category '{category.name}' (likely empty vocabulary). Skipping."))
                continue

            # Calculate cosine similarity between all products in the category
            cosine_sim_matrix = cosine_similarity(tfidf_matrix)

            # Get indices of pairs with similarity above the threshold
            similar_indices = np.argwhere(cosine_sim_matrix > similarity_threshold)

            for pair in similar_indices:
                prod_idx_a, prod_idx_b = pair

                # Ensure we are not comparing a product to itself and avoid duplicate pairs
                if prod_idx_a >= prod_idx_b:
                    continue

                prod_a = products_in_cat[prod_idx_a]
                prod_b = products_in_cat[prod_idx_b]

                # --- Apply Level 3 Conditions ---
                # 1. Different Brands
                if prod_a.brand == prod_b.brand:
                    continue

                # 2. Similar Sizes
                if not size_comparer.are_sizes_compatible(prod_a, prod_b):
                    continue
                
                # 3. Create the substitution
                score = cosine_sim_matrix[prod_idx_a, prod_idx_b]
                _, created = self._create_substitution(
                    prod_a, 
                    prod_b, 
                    level='LVL3',
                    score=score, 
                    source='tfidf_v1'
                )
                if created:
                    new_substitutions_count += 1

        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new Level 3 substitutions."))
