from django.db import models

class Product(models.Model):
    """
    Represents the master or canonical record for a product, independent of
    any single store. This holds the core identifying information.
    """
    name = models.CharField(
        max_length=255,
        help_text="The full name of the product as seen in the store."
    )
    brand = models.CharField(
        max_length=100,
        help_text="The brand of the product, e.g., 'coles', 'Coca-Cola'."
    )
    size = models.CharField(
        max_length=50,
        help_text="The size or quantity of the product, e.g., '500g', '1 Each'."
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="The universal barcode (UPC/EAN) of the product."
    )
    category = models.ForeignKey(
        'stores.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        help_text="The category this product belongs to."
    )
    substitute_goods = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Optional: Other products that can be used as substitutes."
    )

    class Meta:
        unique_together = ('name', 'brand', 'size')

    def __str__(self):
        return f"{self.brand} {self.name} ({self.size})"
