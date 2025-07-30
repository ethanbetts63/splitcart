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
        help_text="The brand of the product, e.g., 'Coles', 'Coca-Cola'."
    )
    size = models.CharField(
        max_length=50,
        help_text="The size or quantity of the product, e.g., '500g', '1 Each'."
    )
    category = models.ForeignKey(
        'store.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        help_text="The category this product belongs to."
    )

    class Meta:
        # Ensures that we don't have duplicate master products
        # A product is unique based on its name, brand, and size.
        unique_together = ('name', 'brand', 'size')

    def __str__(self):
        return f"{self.brand} {self.name} ({self.size})"

