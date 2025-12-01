from django.db import models

class ProductPriceSummary(models.Model):
    """
    Stores aggregated price metrics for a single product to enable fast
    bargain discovery at query time.
    """
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, primary_key=True, related_name='price_summary')

    # The absolute lowest price available for this product, across all stores.
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # The absolute highest price available.
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # The number of different companies that stock this product.
    company_count = models.PositiveIntegerField(default=0, db_index=True)

    # The number of different IGA stores that stock this product.
    iga_store_count = models.PositiveIntegerField(default=0)
    
    # The maximum possible discount percentage for this product globally.
    # Calculated as: ((max_price - min_price) / max_price) * 100
    best_possible_discount = models.IntegerField(db_index=True, null=True)

    class Meta:
        indexes = [
            # Index to quickly find products with high potential discounts.
            models.Index(fields=['-best_possible_discount']),
            models.Index(fields=['company_count']),
        ]

    def __str__(self):
        return f"Summary for {self.product.name}: {self.best_possible_discount}% max discount"
