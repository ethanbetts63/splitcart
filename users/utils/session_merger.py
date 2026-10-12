from django.db import transaction

from users.models import Cart
from .name_generator import generate_unique_name


def merge_anonymous_session(user, anonymous_id):
    """Hand the cart a signed-out browser filled to the account it just entered.

    `anonymous_id` should be the validated `uuid.UUID`, not the string as
    posted: both doors validate it with a `UUIDField` and pass the result, so an
    upper-case spelling of the same identifier finds the same cart at either.

    An empty signed-out cart is left where it is: there is nothing to carry in.

    One transaction, because the first write is destructive. The account's own
    active cart is stood down before the replacement exists, so a failure
    anywhere after that would otherwise leave the shopper with no active cart
    and the list they had switched off.
    """
    if not user or not anonymous_id:
        return

    with transaction.atomic():
        try:
            anon_cart = Cart.objects.get(anonymous_id=anonymous_id, is_active=True)
        except Cart.DoesNotExist:
            return

        # Every signed-out visit gets an active cart from `GET /api/carts/active/`,
        # so a browser that signed out and straight back in arrives holding an
        # empty one. Handing that over would stand the account's own list down
        # for nothing, and from the shopper's side their cart would vanish.
        if not anon_cart.items.exists():
            return

        Cart.objects.filter(user=user, is_active=True).update(is_active=False)

        new_cart_name = "Cart"
        if anon_cart.name != 'Anonymous Cart':
            new_cart_name = anon_cart.name

        unique_cart_name = generate_unique_name(Cart, {'user': user}, new_cart_name)
        new_cart = Cart.objects.create(user=user, name=unique_cart_name, is_active=True)

        anon_cart.items.update(cart=new_cart)
        anon_cart.delete()
