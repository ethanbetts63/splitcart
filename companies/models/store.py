from django.db import models

class Store(models.Model):
    """
    Represents a physical or virtual store where products are sold.
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
    store_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="The unique identifier for the store from the company's own system."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="True if the store is currently being scraped."
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
        db_index=True,
        help_text="The city where the store is located."
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="The state or territory of the store."
    )
    postcode = models.CharField(
        max_length=10,
        blank=True,
        help_text="The postcode of the store."
    )

    class Meta:
        unique_together = ('company', 'store_id')

    def __str__(self):
        return f"{self.name} ({self.company.name})"