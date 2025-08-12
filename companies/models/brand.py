from django.db import models

class Brand(models.Model):
    """
    Represents a specific brand or banner under a parent company.
    e.g., 'Vintage Cellars' is a brand under 'Coles Group'.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the brand."
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='brands',
        help_text="The parent company that owns this brand."
    )
    id = models.CharField(
        max_length=100,
        unique=True,
        primary_key=True,
        help_text="The unique identifier for the brand."
    )
    store_finder_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="The store finder ID for the brand."
    )

    def __str__(self):
        return f"{self.name} ({self.company.name})"