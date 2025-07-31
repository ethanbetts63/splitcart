from django.db import models

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="The name of the category, e.g., 'Fruit & Vegetables'."
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="A URL-friendly version of the name, e.g., 'fruit-vegetables'."
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="The parent category, if this is a subcategory."
    )
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,  # Allow null for top-level, non-store-specific categories
        blank=True,
        help_text="The store this category belongs to, if any."
    )

    class Meta:
        verbose_name_plural = "Categories"
        # The combination of a category's name and its parent must be unique.
        # A null parent indicates a top-level category.
        unique_together = ('name', 'parent')

    def __str__(self):
        # Build the full path for the category, e.g., "Pantry > Snacks > Chips"
        full_path = [self.name]
        p = self.parent
        while p:
            full_path.append(p.name)
            p = p.parent
        return ' > '.join(reversed(full_path))
