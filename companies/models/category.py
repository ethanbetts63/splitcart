from django.db import models
from .category_link import CategoryLink

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
    category_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The category ID from the store's website, if available."
    )
    parents = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='subcategories',
        help_text="The parent categories of this category."
    )
    links = models.ManyToManyField(
        'self',
        through=CategoryLink,
        symmetrical=True, # This can be true now as the model is symmetrical
        blank=True,
        help_text="Links to categories in other companies with a defined relationship type."
    )

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('slug', 'company')

    def __str__(self):
        return self.name
