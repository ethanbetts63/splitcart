import datetime
from django.db import models
from api.utils.price_normalizer import PriceNormalizer

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
    sku = models.CharField(max_length=100, db_index=True)
    
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
    per_unit_price_string = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The raw string for the per unit price, e.g., '$1.68 per 100 g'."
    )
    
    is_on_special = models.BooleanField(default=False)
    is_available = models.BooleanField(
        null=True,
        default=None,
        help_text="Whether the product was in stock at the time of scraping."
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this is the latest price record for the product at this store."
    )
    
    scraped_date = models.DateField()
    
    normalized_key = models.CharField(max_length=255, unique=True, db_index=True)
    

    def clean(self):
        super().clean()
        if self.product_id and self.store_id and self.price and self.scraped_date:
            self.normalized_key = PriceNormalizer.get_normalized_key(
                self.product_id, self.store_id, self.price, self.scraped_date.isoformat()
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-scraped_date']

    def __str__(self):
        return f"{self.product.name} at {self.store.store_name} for ${self.price} on {self.scraped_date}"
