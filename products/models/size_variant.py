from django.db import models

class ProductSizeVariant(models.Model):
    """
    Represents a symmetrical size variant relationship between two products.
    """
    product_a = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='size_variants_a'
    )
    product_b = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='size_variants_b'
    )

    class Meta:
        unique_together = ('product_a', 'product_b')

    def __str__(self):
        return f"{self.product_a} <-> {self.product_b} (Size Variant)"
