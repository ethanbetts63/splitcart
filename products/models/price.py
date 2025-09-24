import datetime
from django.db import models
from data_management.utils.price_normalizer import PriceNormalizer

class Price(models.Model):
    """
    Represents a single, historical price point for a Product at a specific
    Store on a specific date. This is a lightweight pointer to a PriceRecord.
    """
    price_record = models.ForeignKey(
        'PriceRecord',
        on_delete=models.PROTECT,
        related_name="price_entries"
    )
    store = models.ForeignKey(
        'companies.Store',
        on_delete=models.PROTECT,
        related_name="prices"
    )
    sku = models.CharField(max_length=100, db_index=True)
    
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
    
    SOURCE_CHOICES = [
        ('direct_scrape', 'Direct Scrape'),
        ('inferred_group', 'Inferred from Group'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='direct_scrape',
        help_text="How the price was obtained: from a direct scrape or inferred from a group ambassador."
    )
    
    scraped_date = models.DateField()
    
    normalized_key = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        ordering = ['-scraped_date']

    def __str__(self):
        return f"{self.price_record.product.name} at {self.store.store_name} on {self.scraped_date}"

    def save(self, *args, **kwargs):
        if self.price_record and self.price_record.product_id and self.store_id and self.price_record.price and self.scraped_date:
            price_data = {
                'product_id': self.price_record.product_id,
                'store_id': self.store_id,
                'price': self.price_record.price,
                'date': self.scraped_date.isoformat()
            }
            normalizer = PriceNormalizer(price_data=price_data, company=self.store.company.name)
            self.normalized_key = normalizer.get_normalized_key()
        super().save(*args, **kwargs)