from itertools import combinations
from products.models import Product, ProductBrand, ProductSubstitution

class BaseSubstitutionGenerator:
    """
    Base class for different substitution generation strategies.
    """
    def __init__(self, command):
        self.command = command

    def generate(self):
        """The main method to find and create substitutions."""
        raise NotImplementedError("Subclasses must implement the 'generate' method.")

    def _create_substitution(self, product_a, product_b, type, score, source):
        """
        Creates a symmetrical substitution entry in the database, ensuring no duplicates.
        The product with the lower ID is always stored as product_a to prevent duplicates like (A,B) and (B,A).
        """
        if product_a.id == product_b.id:
            return None, False

        if product_a.id > product_b.id:
            product_a, product_b = product_b, product_a

        sub, created = ProductSubstitution.objects.update_or_create(
            product_a=product_a,
            product_b=product_b,
            defaults={
                'type': type,
                'score': score,
                'source': source
            }
        )
        return sub, created

class SizeSubstitutionGenerator(BaseSubstitutionGenerator):
    """
    Generates substitutions for Level 1: Same brand, same product, different size.
    """
    def generate(self):
        self.command.stdout.write("--- Generating Level 1: Size Substitutions ---")
        
        brands = ProductBrand.objects.all()
        new_substitutions_count = 0

        for brand in brands:
            products = Product.objects.filter(brand=brand.name)
            if products.count() < 2:
                continue

            # Group products by a "base name" to identify size variants
            base_product_groups = self._group_by_base_name(products)

            for group in base_product_groups.values():
                if len(group) > 1:
                    # Create substitutions for all pairs within the group
                    for prod_a, prod_b in combinations(group, 2):
                        _, created = self._create_substitution(
                            prod_a, 
                            prod_b, 
                            type='SIZE', 
                            score=0.95, 
                            source='size_heuristic_v1'
                        )
                        if created:
                            new_substitutions_count += 1
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Generated {new_substitutions_count} new size substitutions."))

    def _group_by_base_name(self, products):
        """
        Groups products by a generated 'base name'.
        
        NOTE: This is a simple heuristic and the weak point of this generator.
        A more sophisticated size-parsing and removal utility would make this much more accurate.
        """
        groups = {}
        for product in products:
            # A simple heuristic: use the first 3 words of the product name as the base name.
            # This will work for names like "Coca-Cola Classic 1.25L" but may fail for others.
            base_name = " ".join(product.name.split()[:3])
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(product)
        return groups
