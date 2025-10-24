import uuid
from django.db import models
from products.models import Product
from users.models.cart_item import CartItem

class CartSubstitution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # This links to the specific CartItem that is being substituted
    original_cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name='chosen_substitutions',
        help_text="The CartItem that this substitution is replacing"
    )
    # This is the product chosen as a substitute
    substituted_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='substitutes_chosen_for_items',
        help_text="The actual substitute product chosen"
    )
    # This is the quantity of the substituted_product
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Cart Substitution"
        verbose_name_plural = "Cart Substitutions"
        # A specific original_cart_item can only have one substituted_product chosen for it
        unique_together = ('original_cart_item', 'substituted_product')

    def __str__(self):
        return (
            f"{self.quantity} x {self.substituted_product.name} "
            f"for {self.original_cart_item.quantity} x {self.original_cart_item.product.name} "
            f"in {self.original_cart_item.cart.name}"
        )