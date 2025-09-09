from itertools import combinations
from collections import defaultdict
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product, ProductBrand
from api.utils.product_normalizer import ProductNormalizer

class StrictSubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 1: Same product, different size.
    This is a high-accuracy generator that requires names to match exactly.
    """
    def generate(self):
        self.command.stdout.write("--- Generating Level 1: Strict Substitutions (Exact Name Match) ---")
        
        new_substitutions_count = 0

        # 1. Build a map where keys are normalized names and values are lists of products.
        # This will group all products that share at least one common normalized name.
        name_map = defaultdict(list)
        products = Product.objects.prefetch_related('name_variations').all()

        for product in products:
            # Create a set of all possible normalized names for the product.
            known_names = {product.normalized_name}
            if product.name_variations:
                for name_variation, store in product.name_variations:
                    # Normalize each variation on the fly.
                    # We only use the 'name' for normalization, ignoring brand/size context here.
                    normalizer = ProductNormalizer({'name': name_variation})
                    known_names.add(normalizer.get_fully_normalized_name())
            
            # Add the product to the map for each of its known names.
            for name in known_names:
                if name:
                    name_map[name].append(product)

        # 2. Process the groups of identical products.
        for name, product_group in name_map.items():
            if len(product_group) > 1:
                # Remove duplicate products from the group (a product might be added multiple times
                # if it has multiple names that map to the same normalized name).
                unique_products = list(set(product_group))
                
                if len(unique_products) > 1:
                    # TODO: Add size comparison logic here.
                    # For now, we link all pairs in the group.
                    # Future logic should check `standardized_sizes` and only link
                    # products with different, but comparable, physical sizes.

                    for prod_a, prod_b in combinations(unique_products, 2):
                        _, created = self._create_substitution(
                            prod_a, 
                            prod_b, 
                            type='STRICT', # Using a new type to distinguish from the old fuzzy match
                            score=1.0, 
                            source='strict_name_match_v1'
                        )
                        if created:
                            new_substitutions_count += 1
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new strict substitutions."))
