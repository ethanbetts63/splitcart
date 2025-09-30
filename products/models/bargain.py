from django.db import models
from .product import Product
from .price import Price
from companies.models.store import Store

class Bargain(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bargain_records')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='bargains')
    cheapest_price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name='bargain_as_cheapest')
    most_expensive_price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name='bargain_as_most_expensive')
    percentage_difference = models.FloatField()

    class Meta:
        unique_together = ('product', 'store')

    def __str__(self):
        return f"{self.product.name} at {self.store.name} ({self.percentage_difference:.0f}% cheaper)"
