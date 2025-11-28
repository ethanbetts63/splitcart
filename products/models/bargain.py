from django.db import models
from companies.models import Store

class Bargain(models.Model):
    """
    Represents a pre-calculated price difference between two Price objects for a specific product.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='bargains')
    discount_percentage = models.IntegerField()
    cheaper_price = models.ForeignKey('products.Price', on_delete=models.CASCADE, related_name='bargains_as_cheaper')
    expensive_price = models.ForeignKey('products.Price', on_delete=models.CASCADE, related_name='bargains_as_expensive')

    # Denormalized fields for performance
    cheaper_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='bargains_as_cheaper_store')
    expensive_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='bargains_as_expensive_store')

    class Meta:
        """
        Meta options for the Bargain model.
        """
        unique_together = ('product', 'cheaper_price', 'expensive_price')
        indexes = [
            models.Index(fields=['product', '-discount_percentage']),
            # Index for the new high-performance query
            models.Index(fields=['cheaper_store', 'expensive_store', '-discount_percentage']),
        ]

    def __str__(self):
        # The __str__ method should return a string.
        return f"Product {self.product_id} ({self.discount_percentage}% off)"
