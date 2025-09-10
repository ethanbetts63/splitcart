from products.models import ProductSubstitution

class BaseSubstitutionGenerator:
    """
    Base class for different substitution generation strategies.
    """
    def __init__(self, command):
        self.command = command

    def generate(self):
        """The main method to find and create substitutions."""
        raise NotImplementedError("Subclasses must implement the 'generate' method.")

    def _create_substitution(self, product_a, product_b, level, score, source):
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
                'level': level,
                'score': score,
                'source': source
            }
        )
        return sub, created
