from django.db import models


class PriceQuerySet(models.QuerySet):
    def for_stores(self, store_ids):
        """
        Filters prices to those available at the given stores, automatically
        resolving member store IDs to their group anchor IDs. Price rows only
        exist on anchors — member prices are deleted after group confirmation.
        """
        from products.utils.get_pricing_stores import get_pricing_stores_map
        pricing_map = get_pricing_stores_map(store_ids)
        anchor_ids = list(set(pricing_map.values()))
        return self.filter(store_id__in=anchor_ids)


class Price(models.Model):
    objects = PriceQuerySet.as_manager()
    """
    Represents the single, most recent price for a Product at a specific Store.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    store = models.ForeignKey(
        'companies.Store',
        on_delete=models.CASCADE,
        related_name="prices"
    )
    
    # Price details
    scraped_date = models.DateField(db_index=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    was_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    save_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        db_index=True
    )
    unit_of_measure = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    per_unit_price_string = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    is_on_special = models.BooleanField(default=False)
    price_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        unique_together = ('product', 'store')
        ordering = ['product__name']
        indexes = [
            models.Index(fields=['store', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} at {self.store.store_name} - ${self.price}"