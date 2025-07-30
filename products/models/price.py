from django.db import models

class Price(models.Model):
    """
    Represents a single, historical price point for a Product at a specific
    Store on a specific date. A new record is created for each scrape.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name="prices",
        help_text="The master product this price point belongs to."
    )
    # Using a string reference 'store.Store' to avoid circular imports.
    store = models.ForeignKey(
        'store.Store',
        on_delete=models.CASCADE,
        related_name="prices",
        help_text="The store where this price was recorded."
    )
    # The unique ID or SKU that the specific store uses for this product.
    # This is the most reliable way to find the same item in future scrapes.
    store_product_id = models.CharField(max_length=100, db_index=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The price of the product at the time of scraping."
    )
    scraped_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time this price was recorded."
    )
    is_on_special = models.BooleanField(
        default=False,
        help_text="True if the product was marked as on special."
    )
    offer_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="A description of the special offer, e.g., 'Buy 4 for $6'."
    )
    url = models.URLField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="A direct link to the product page on the store's website."
    )

    class Meta:
        ordering = ['-scraped_at'] # Show the most recent prices first by default

    def __str__(self):
        # We can still access related models via self.product and self.store
        return f"{self.product.name} at {self.store.name} for ${self.price} on {self.scraped_at.date()}"
