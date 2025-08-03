from django.db import models

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="The name of the category, e.g., 'Fruit & Vegetables'."
    )
    slug = models.SlugField(
        max_length=120,
        help_text="A URL-friendly version of the name, e.g., 'fruit-vegetables'."
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='categories',
        help_text="The company that this category belongs to."
    )
    store_category_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The category ID from the store's website, if available."
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="The parent category, if this is a subcategory."
    )

    class Meta:
        verbose_name_plural = "Categories"
        # A category's name, its parent, and its company must be unique together.
        unique_together = ('name', 'parent', 'company')
        # A company can't have two categories with the same slug
        unique_together = ('slug', 'company')

    def __str__(self):
        # Build the full path for the category, e.g., "Pantry > Snacks > Chips"
        full_path = [self.name]
        p = self.parent
        while p:
            full_path.append(p.name)
            p = p.parent
        return ' > '.join(reversed(full_path))
