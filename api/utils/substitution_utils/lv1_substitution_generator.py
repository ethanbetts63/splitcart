from itertools import combinations
from collections import defaultdict
from .substitution_generator import BaseSubstitutionGenerator
from products.models import Product, ProductBrand
from .size_comparer import SizeComparer

class Lvl1SubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 1: Same product, different size.
    This is a high-accuracy generator that requires names to match exactly.
    """
    def generate(self):
        level_definition = "Same brand, same product, different size."
        self.command.stdout.write(f"--- Generating Level 1: {level_definition} ---")
        
        new_substitutions_count = 0
        size_comparer = SizeComparer()

        brands = ProductBrand.objects.all()

        for brand in brands:
            name_map = defaultdict(list)
            products = Product.objects.filter(brand=brand.name)

            for product in products:
                variation_names = {item[0] for item in product.name_variations if isinstance(item, list) and len(item) > 0} if product.name_variations else set()
                all_normalized_names = {product.normalized_name}.union(variation_names)
                
                for name in all_normalized_names:
                    if name:
                        name_map[name].append(product)

            for name, product_group in name_map.items():
                if len(product_group) > 1:
                    unique_products = list(set(product_group))
                    
                    if len(unique_products) > 1:
                        for prod_a, prod_b in combinations(unique_products, 2):
                            sizes_a = size_comparer.get_canonical_sizes(prod_a)
                            sizes_b = size_comparer.get_canonical_sizes(prod_b)

                            if sizes_a and sizes_b and sizes_a != sizes_b:
                                _, created = self._create_substitution(
                                    prod_a, 
                                    prod_b, 
                                    level='LVL1',
                                    score=1.0, 
                                    source='strict_name_match_v1'
                                )
                                if created:
                                    new_substitutions_count += 1
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new Level 1 substitutions."))
