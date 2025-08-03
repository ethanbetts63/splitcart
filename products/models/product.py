from django.db import models

class Product(models.Model):
    """
    Represents a specific product sold at a specific store.
    This record connects the what (the product details) with the where (the store).
    """
    name = models.CharField(
        max_length=255,
        help_text="The full name of the product as seen in the store."
    )
    brand = models.CharField(
        max_length=100,
        help_text="The brand of the product, e.g., 'Coles', 'Coca-Cola'."
    )
    size = models.CharField(
        max_length=50,
        help_text="The size or quantity of the product, e.g., '500g', '1 Each'."
    )
    store = models.ForeignKey(
        'companies.Store',
        on_delete=models.CASCADE,
        related_name="products",
        help_text="The store where this specific product is sold."
    )
    category = models.ForeignKey(
        'companies.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        help_text="The category this product belongs to."
    )
    barcode = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="The universal barcode (UPC/EAN) of the product."
    )
    substitute_goods = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Optional: Other products that can be used as substitutes."
    )

    class Meta:
        # A product is unique based on its name, brand, size, and the store it's sold in.
        unique_together = ('name', 'brand', 'size', 'store')

    def __str__(self):
        return f"{self.brand} {self.name} ({self.size}) at {self.store.name}"
