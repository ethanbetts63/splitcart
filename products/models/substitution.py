from django.db import models

class ProductSubstitution(models.Model):
    """
    Represents a Symmetrical substitution relationship between two products,
    ranked by a similarity score and classified by type.
    """
    SUBSTITUTION_TYPES = [
        ('SIZE', 'Same product, different size'),
        ('VARIANT', 'Same brand, similar product'),
        ('COMPETITOR', 'Different brand, similar product'),
        ('OTHER', 'Other/Unknown'),
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

    type = models.CharField(
        max_length=20, 
        choices=SUBSTITUTION_TYPES, 
        db_index=True,
        help_text="The classification of the substitution type based on heuristics.",
        default='OTHER'
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
        return f"{self.product_a} <-> {self.product_b} (Type: {self.get_type_display()}, Score: {self.score})"
