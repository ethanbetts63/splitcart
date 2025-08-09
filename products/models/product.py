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
    category = models.ManyToManyField(
        'companies.Category',
        related_name="products",
        help_text="The categories this product belongs to."
    )
    barcode = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="The universal barcode (UPC/EAN) of the product."
    )
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    allergens = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    nutritional_information = models.JSONField(blank=True, null=True)
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
