from django.db import models
from django.db.models import Q
import re
from companies.models.category import Category

class Product(models.Model):
    """
    Represents a specific product sold at a specific store.
    This record connects the what (the product details) with the where (the store).
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The full name of the product as seen in the store."
    )
    brand = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="The brand of the product, e.g., 'Coles', 'Coca-Cola'."
    )
    size = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="The size or quantity of the product, e.g., '500g', '1 Each'."
    )
    category = models.ManyToManyField(
        Category,
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
    url = models.URLField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    allergens = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    substitute_goods = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text="Optional: Other products that can be used as substitutes."
    )
    size_variants = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text="Products that are the same item but in a different size."
    )

    normalized_name_brand_size = models.CharField(
        max_length=500,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Normalized combination of name, brand, and size for uniqueness."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['barcode'],
                condition=Q(barcode__isnull=False) & ~Q(barcode=''),
                name='unique_barcode_if_not_null_or_empty'
            ),
            models.UniqueConstraint(
                fields=['normalized_name_brand_size'],
                condition=Q(normalized_name_brand_size__isnull=False),
                name='unique_normalized_name_brand_size'
            )
        ]

    def _clean_value(self, value):
        if value is None:
            return ''
        # Remove non-alphanumeric characters and spaces
        cleaned_value = re.sub(r'[^a-z0-9]', '', str(value).lower())
        return cleaned_value

    def save(self, *args, **kwargs):
        # Generate normalized_name_brand_size before saving
        self.normalized_name_brand_size = self._clean_value(self.name) + \
                                          self._clean_value(self.brand) + \
                                          self._clean_value(self.size)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.name} ({self.size})"
