from django.db import models

class ProductSubstitution(models.Model):
    """
    Represents a Symmetrical substitution relationship between two products,
    ranked by a similarity score and classified by level.
    """
    SUBSTITUTION_LEVELS = [
        ('LVL1', 'Same brand, same product, different size.'),
        ('LVL2', 'Same brand, similar product, similar size.'),
        ('LVL3', 'Different brand, similar product, similar size.'),
        ('LVL4', 'Different brand, similar product, different size.'),
        ('LVL5', 'Same category, semantic match.'),
        ('LVL6', 'Linked category, semantic match.'),
        ('LVL7', 'Close-linked category, semantic match.'),
        ('LVL8', 'Distant-linked category, semantic match.'),
    ]

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

    level = models.CharField(
        max_length=20, 
        choices=SUBSTITUTION_LEVELS, 
        db_index=True,
        help_text="The classification of the substitution level based on heuristics.",
        default='LVL4'
    )
    score = models.FloatField(
        db_index=True,
        help_text="Confidence score from 0.0 to 1.0, indicating the quality of the match."
    )
    source = models.CharField(
        max_length=50, 
        help_text="How this substitution was generated (e.g., 'heuristic_v1', 'manual').",
        default='unknown'
    )

    class Meta:
        # Ensure we don't have duplicate substitution entries.
        # A check constraint in the database or a custom save method
        # would be needed to enforce that (A, B) is the same as (B, A).
        unique_together = ('product_a', 'product_b')
        ordering = ['-score']

    def __str__(self):
        return f"{self.product_a} <-> {self.product_b} (Level: {self.get_level_display()}, Score: {self.score})"
