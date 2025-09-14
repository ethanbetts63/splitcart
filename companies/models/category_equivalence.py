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
