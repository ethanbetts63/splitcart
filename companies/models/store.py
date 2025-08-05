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
    address = models.CharField(
        max_length=255,
        blank=True,
        help_text="The street address of the store."
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,  # We will likely want to query stores by city
        help_text="The city where the store is located."
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,  # And also by state
        help_text="The state or territory of the store."
    )

    class Meta:
        unique_together = ('name', 'company')

    def __str__(self):
        return f"{self.name} ({self.company.name})"
