from django.db import models

class Category(models.Model):
    """
    Represents a product category, used for organizing products.
    """
    name = models.CharField(
        max_length=100,
        help_text="The name of the category, e.g., 'Fruit & Vegetables'."
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="A URL-friendly version of the name, e.g., 'fruit-vegetables'."
    )
    url_path = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="Optional: The specific URL path for this category if it's not based on the slug."
    )
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="The store this category belongs to."
    )

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('name', 'store')

    def __str__(self):
        return f"{self.name} ({self.store.name})"
