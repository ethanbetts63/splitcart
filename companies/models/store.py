from django.db import models

class Store(models.Model):
    """
    Represents a physical or virtual store where products are sold.
    For national brands like Coles, this might be a single 'National' store.
    For brands like IGA, this will be an individual store location.
    """
    name = models.CharField(
        max_length=100,
        help_text="The specific name of the store, e.g., 'IGA Cannington' or 'Coles National'."
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='stores',
        help_text="The parent company that owns this store."
    )
    base_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="The base URL of the specific store, if applicable."
    )

    class Meta:
        unique_together = ('name', 'company')

    def __str__(self):
        return f"{self.name} ({self.company.name})"
