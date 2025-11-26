from django.db import models

class Bargain(models.Model):
    """
    Represents a pre-calculated price difference between two stores for a specific product.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='bargains')
    discount_percentage = models.IntegerField()
    cheaper_store = models.ForeignKey('companies.Store', on_delete=models.CASCADE, related_name='cheaper_bargains')
    expensive_store = models.ForeignKey('companies.Store', on_delete=models.CASCADE, related_name='expensive_bargains')

    class Meta:
        """
        Meta options for the Bargain model.
        """
        # Indexing these fields will be crucial for fast lookups at query time.
        indexes = [
            models.Index(fields=['cheaper_store', 'expensive_store', '-discount_percentage']),
            models.Index(fields=['product']),
        ]
        # A product can have the same bargain (e.g., 20% off between Coles and Woolies) only once.
        unique_together = ('product', 'cheaper_store', 'expensive_store')

    def __str__(self):
        # The __str__ method should return a string, so we need to handle the case where related objects might not be loaded.
        # This is more for debugging and admin display.
        return f"{self.product_id} ({self.discount_percentage}% off at {self.cheaper_store_id} vs {self.expensive_store_id})"
