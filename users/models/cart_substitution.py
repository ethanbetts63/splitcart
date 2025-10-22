import uuid
from django.db import models
from products.models import Product
from users.models.cart_item import CartItem

class CartSubstitution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='substitutions')
    original_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='substituted_by',
        help_text="The original product this is substituting for"
    )
    substituted_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='substitutes_for',
        help_text="The actual substitute product chosen"
    )
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart Substitution"
        verbose_name_plural = "Cart Substitutions"
        unique_together = ('cart_item', 'substituted_product')

    def __str__(self):
        return f"{self.quantity} x {self.substituted_product.name} for {self.original_product.name} in {self.cart_item.cart.name}"
