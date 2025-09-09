from itertools import combinations
from thefuzz import fuzz
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product, ProductBrand
from api.utils.product_normalizer import ProductNormalizer

class VariantSubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 2: Same brand, similar product, similar size.
    """
    def generate(self):
        self.command.stdout.write("--- Generating Level 2: Variant Substitutions ---")
        
        brands = ProductBrand.objects.all()
        new_substitutions_count = 0

        for brand in brands:
            products = list(Product.objects.filter(brand=brand.name))
            if len(products) < 2:
                continue

            # Use combinations to check every pair of products for the brand
            for prod_a, prod_b in combinations(products, 2):
                
                # 1. Check for Name Similarity
                # We are looking for a score that is high, but not high enough to be a size variant.
                # This range helps capture variants like "Classic" vs "No Sugar".
                name_similarity = fuzz.token_set_ratio(
                    prod_a.normalized_name, 
                    prod_b.normalized_name
                )
                
                if not (75 < name_similarity <= 90):
                    continue

                # 2. Check for Size Similarity
                # For v1, we define "similar size" as "identical size".
                # This is a performance consideration, as it avoids complex parsing.
                norm_a = ProductNormalizer(prod_a.__dict__)
                norm_b = ProductNormalizer(prod_b.__dict__)
                
                if norm_a.standardized_sizes != norm_b.standardized_sizes:
                    continue

                # If both checks pass, create the substitution
                _, created = self._create_substitution(
                    prod_a,
                    prod_b,
                    type='VARIANT',
                    score=0.85, # A high score, but less than a size-only substitute
                    source='variant_similarity_v1'
                )
                if created:
                    new_substitutions_count += 1
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new variant substitutions."))
