from django.db import models

class Store(models.Model):
    """
    Represents a supermarket or retailer where products are sold.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the store, e.g., 'coles', 'woolworths'."
    )
    base_url = models.URLField(
        max_length=255,
        help_text="The base URL of the store's website."
    )

    def __str__(self):
        return self.name
