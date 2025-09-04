from django.db import models

class ProductSubstitution(models.Model):
    """
    Represents a Symmetrical substitution relationship between two products,
    ranked by a similarity score.
    """
    product_a = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='substitutions_a'
    )
    product_b = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='substitutions_b'
    )

    # The calculated similarity score. The higher, the better the match.
    score = models.FloatField(db_index=True)

    class Meta:
        # Ensure we don't have duplicate substitution entries.
        # A check constraint in the database or a custom save method
        # would be needed to enforce that (A, B) is the same as (B, A).
        unique_together = ('product_a', 'product_b')
        ordering = ['-score']

    def __str__(self):
        return f"{self.product_a} <-> {self.product_b} (Score: {self.score})"
