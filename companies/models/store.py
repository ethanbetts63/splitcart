from django.db import models

class Store(models.Model):
    """
    Represents a physical or virtual store where products are sold.
    """
    # Existing fields
    name = models.CharField(
        max_length=255,  # Increased max_length for longer store names
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
    division = models.CharField(
        max_length=100,
        blank=True,
        help_text="The division the store belongs to, e.g., 'Supermarkets'."
    )
    description = models.TextField(
        blank=True,
        help_text="A longer description of the store, if available."
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="The contact phone number for the store."
    )
    fax_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="The contact fax number for the store."
    )
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        help_text="The first line of the store's address."
    )
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="The second line of the store's address."
    )
    suburb = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="The suburb where the store is located."
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
    country = models.CharField(
        max_length=50,
        default='Australia',
        help_text="The country where the store is located."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="The latitude of the store's location."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="The longitude of the store's location."
    )
    trading_hours = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing the store's trading hours."
    )
    facilities = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing a list of store facilities."
    )
    is_trading = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates if the store is currently trading."
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        help_text="The specific brand of the store, e.g., 'Coles Supermarkets'."
    )
    online_shop_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="The URL for the store's online shopping portal."
    )

    class Meta:
        unique_together = ('company', 'store_id')
        verbose_name = "Store"
        verbose_name_plural = "Stores"

    def __str__(self):
        return f"{self.name} ({self.company.name})"