from django.db import models

class Price(models.Model):
    """
    Represents a single, historical price point for a Product at a specific
    Store on a specific date. A new record is created for each scrape.
    """
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE,
        related_name="prices"
    )
    store = models.ForeignKey(
        'companies.Store',
        on_delete=models.PROTECT,
        related_name="prices"
    )
    store_product_id = models.CharField(max_length=100, db_index=True)
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The current price of the product."
    )
    was_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The previous price if the item is on special."
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The price per standard unit (e.g., per 100g, per 1L)."
    )
    unit_of_measure = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The standard unit for the unit_price, e.g., '100g', '1L'."
    )
    
    is_on_special = models.BooleanField(default=False)
    is_available = models.BooleanField(
        default=True,
        help_text="Whether the product was in stock at the time of scraping."
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this is the latest price record for the product at this store."
    )
    
    scraped_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        ordering = ['-scraped_at']

    def __str__(self):
        return f"{self.product.name} at {self.store.name} for ${self.price} on {self.scraped_at.date()}"
