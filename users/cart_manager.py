from users.models import Cart

class CartManager:
    def get_active_cart(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(
                user=request.user, is_active=True,
                defaults={'name': f"{request.user.email}'s Cart"}
            )
            return cart
        elif hasattr(request, 'anonymous_id'):
            cart, _ = Cart.objects.get_or_create(
                anonymous_id=request.anonymous_id, is_active=True,
                defaults={'name': 'Anonymous Cart'}
            )
            return cart
        return None

    def switch_active_cart(self, user, cart_id):
        Cart.objects.filter(user=user, is_active=True).update(is_active=False)
        new_active_cart = Cart.objects.get(user=user, pk=cart_id)
        new_active_cart.is_active = True
        new_active_cart.save()
        return new_active_cart

    def create_cart(self, request, name, is_active=True):
        if request.user.is_authenticated:
            if is_active:
                Cart.objects.filter(user=request.user, is_active=True).update(is_active=False)
            return Cart.objects.create(user=request.user, name=name, is_active=is_active)
        elif hasattr(request, 'anonymous_id'):
            if is_active:
                Cart.objects.filter(anonymous_id=request.anonymous_id, is_active=True).update(is_active=False)
            return Cart.objects.create(anonymous_id=request.anonymous_id, name=name, is_active=is_active)
        return None

    def rename_cart(self, cart, new_name):
        cart.name = new_name
        cart.save()
        return cart

    def delete_cart(self, cart):
        cart.delete()