from itertools import combinations
from collections import defaultdict
from itertools import combinations
from collections import defaultdict
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product, ProductBrand
from api.utils.product_normalizer import ProductNormalizer
from .size_comparer import SizeComparer

class StrictSubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 1: Same product, different size.
    This is a high-accuracy generator that requires names to match exactly.
    """
    def generate(self):
        self.command.stdout.write("--- Generating Level 1: Strict Substitutions (Exact Name Match) ---")
        
        new_substitutions_count = 0
        size_comparer = SizeComparer()

        # 1. Build a map where keys are normalized names and values are lists of products.
        # This will group all products that share at least one common normalized name.
        name_map = defaultdict(list)
        products = Product.objects.all()

        for product in products:
            # Use the product's own normalized_name and its list of variations.
            all_normalized_names = {product.normalized_name}.union(set(product.name_variations or []))
            
            for name in all_normalized_names:
                if name:
                    name_map[name].append(product)

        # 2. Process the groups of identical products.
        for name, product_group in name_map.items():
            if len(product_group) > 1:
                # Remove duplicate products from the group (a product might be added multiple times
                # if it has multiple names that map to the same normalized name).
                unique_products = list(set(product_group))
                
                if len(unique_products) > 1:
                    for prod_a, prod_b in combinations(unique_products, 2):
                        sizes_a = size_comparer.get_canonical_sizes(prod_a)
                        sizes_b = size_comparer.get_canonical_sizes(prod_b)

                        if sizes_a and sizes_b and sizes_a != sizes_b:
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
