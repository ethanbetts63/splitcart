from django.db import models

class SKU(models.Model):
    """
    Links a Product to a Company with a specific SKU (Stock Keeping Unit).
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='skus'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='skus'
    )
    sku = models.CharField(
        max_length=100,
        db_index=True
    )

    class Meta:
        # A SKU should be unique for a given company.
        unique_together = (('company', 'sku'),)

    def __str__(self):
        return f"{self.company.name} SKU for {self.product.name}: {self.sku}"
