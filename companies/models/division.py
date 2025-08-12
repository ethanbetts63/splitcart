from django.db import models

class Division(models.Model):
    """
    Represents a specific division or banner under a parent company.
    e.g., 'Vintage Cellars' is a division under 'Coles Group'.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the division."
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='divisions',
        help_text="The parent company that owns this division."
    )
    id = models.CharField(
        max_length=100,
        unique=True,
        primary_key=True,
        help_text="The unique identifier for the division."
    )
    store_finder_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="The store finder ID for the division."
    )

    def __str__(self):
        return f"{self.name} ({self.company.name})"
