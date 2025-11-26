from django.db import models

class Bargain(models.Model):
    """
    Represents a pre-calculated price difference between two Price objects for a specific product.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='bargains')
    discount_percentage = models.IntegerField()
    cheaper_price = models.ForeignKey('products.Price', on_delete=models.CASCADE, related_name='bargains_as_cheaper')
    expensive_price = models.ForeignKey('products.Price', on_delete=models.CASCADE, related_name='bargains_as_expensive')

    class Meta:
        """
        Meta options for the Bargain model.
        """
        unique_together = ('product', 'cheaper_price', 'expensive_price')
        indexes = [
            models.Index(fields=['product', '-discount_percentage']),
        ]

    def __str__(self):
        # The __str__ method should return a string.
        return f"Product {self.product_id} ({self.discount_percentage}% off)"
