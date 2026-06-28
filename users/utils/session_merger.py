from users.models import Cart
from .name_generator import generate_unique_name


def merge_anonymous_session(user, anonymous_id):
    if not user or not anonymous_id:
        return

    try:
        anon_cart = Cart.objects.get(anonymous_id=anonymous_id, is_active=True)

        Cart.objects.filter(user=user, is_active=True).update(is_active=False)

        new_cart_name = "Cart"
        if anon_cart.name != 'Anonymous Cart':
            new_cart_name = anon_cart.name

        unique_cart_name = generate_unique_name(Cart, {'user': user}, new_cart_name)
        new_cart = Cart.objects.create(user=user, name=unique_cart_name, is_active=True)

        anon_cart.items.update(cart=new_cart)
        anon_cart.delete()

    except Cart.DoesNotExist:
        pass
