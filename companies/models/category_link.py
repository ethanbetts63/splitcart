from django.db import models

class CategoryLink(models.Model):
    category_a = models.ForeignKey(
        'Category', 
        on_delete=models.CASCADE, 
        related_name='links_a'
    )
    category_b = models.ForeignKey(
        'Category', 
        on_delete=models.CASCADE, 
        related_name='links_b'
    )

    class LinkType(models.TextChoices):
        MATCH = 'MATCH', 'Match'
        CLOSE_RELATION = 'CLOSE', 'Close Relation'
        DISTANT_RELATION = 'DISTANT', 'Distant Relation'

    link_type = models.CharField(
        max_length=10, 
        choices=LinkType.choices,
        help_text="The type or strength of the link between the two categories."
    )

    class Meta:
        # Ensure that we don't have duplicate links in either direction.
        # A constraint is better than overriding save() for bulk operations.
        constraints = [
            models.UniqueConstraint(
                fields=['category_a', 'category_b'], 
                name='unique_category_link'
            )
        ]

    def __str__(self):
        return f"{self.category_a.name} <-> {self.category_b.name} ({self.get_link_type_display()})"
