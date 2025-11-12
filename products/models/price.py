from django.db import models

class Price(models.Model):
    """
    Represents the single, most recent price for a Product at a specific Store.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    store = models.ForeignKey(
        'companies.Store',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    
    # Price details
    scraped_date = models.DateField()
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
    price_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        unique_together = ('product', 'store')
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product.name} at {self.store.store_name} - ${self.price}"