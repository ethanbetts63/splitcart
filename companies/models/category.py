from django.db import models

class CategoryEquivalence(models.Model):
    from_category = models.ForeignKey(
        'Category', 
        on_delete=models.CASCADE, 
        related_name='from_equivalences'
    )
    to_category = models.ForeignKey(
        'Category', 
        on_delete=models.CASCADE, 
        related_name='to_equivalences'
    )

    class RelationshipType(models.TextChoices):
        EQUIVALENT = 'EQ', 'Equivalent'
        IS_SUBSET_OF = 'SUB', 'Is Subset Of'

    relationship_type = models.CharField(
        max_length=3, 
        choices=RelationshipType.choices,
        help_text="'Equivalent' is a symmetrical relationship. 'Is Subset Of' is a directed relationship (e.g., from_category is a subset of to_category)."
    )

    class Meta:
        unique_together = ('from_category', 'to_category')

    def __str__(self):
        return f"{self.from_category.name} -> {self.to_category.name} ({self.get_relationship_type_display()})"


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

    equivalences = models.ManyToManyField(
        'self',
        through=CategoryEquivalence,
        symmetrical=False,
        blank=True,
        help_text="Links to categories in other companies with a defined relationship type."
    )

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('slug', 'company')

    def __str__(self):
        return self.name