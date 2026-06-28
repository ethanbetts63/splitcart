from django.db import models


class Price(models.Model):
    """
    Represents the single, most recent price for a Product at a company.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    
    # Price details
    scraped_date = models.DateField(db_index=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    was_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    save_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        db_index=True
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
        unique_together = ('product', 'company')
        ordering = ['product__name']
        indexes = [
            models.Index(fields=['company', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} at {self.company.name} - ${self.price}"
