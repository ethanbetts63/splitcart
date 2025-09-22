from django.db import models

class PriceRecord(models.Model):
    """
    Represents a single, unique combination of price details for a product.
    This is the source of truth for the price data itself, reducing duplication.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name="price_records"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    was_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    unit_of_measure = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    per_unit_price_string = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    is_on_special = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            'product', 'price', 'was_price', 'unit_price',
            'unit_of_measure', 'per_unit_price_string', 'is_on_special'
        ]
        verbose_name = "Price Record"
        verbose_name_plural = "Price Records"

    def __str__(self):
        return f"{self.product.name} - ${self.price}"
