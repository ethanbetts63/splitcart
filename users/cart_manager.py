from django.db import IntegrityError
from users.models import Cart, SelectedStoreList

class CartManager:
    def get_active_cart(self, request):
        created = False
        cart = None
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=request.user, is_active=True,
                defaults={'name': f"{request.user.email}'s Cart"}
            )
        elif hasattr(request, 'anonymous_id'):
            cart, created = Cart.objects.get_or_create(
                anonymous_id=request.anonymous_id, is_active=True,
                defaults={'name': 'Anonymous Cart'}
            )
        else:
            return None

        if created:
            store_list = None
            if request.user.is_authenticated:
                store_list = SelectedStoreList.objects.filter(user=request.user).order_by('-last_used_at').first()
            elif hasattr(request, 'anonymous_id'):
                store_list = SelectedStoreList.objects.filter(anonymous_id=request.anonymous_id).order_by('-last_used_at').first()
            
            if store_list:
                cart.selected_store_list = store_list
                cart.save()

        return cart

    def switch_active_cart(self, user, cart_id):
        Cart.objects.filter(user=user, is_active=True).update(is_active=False)
        new_active_cart = Cart.objects.get(user=user, pk=cart_id)
        new_active_cart.is_active = True
        new_active_cart.save()
        return new_active_cart

    def create_cart(self, request, is_active=True):
        user = request.user if request.user.is_authenticated else None
        anonymous_id = getattr(request, 'anonymous_id', None)

        if not user and not anonymous_id:
            return None

        if is_active:
            if user:
                Cart.objects.filter(user=user, is_active=True).update(is_active=False)
            elif anonymous_id:
                Cart.objects.filter(anonymous_id=anonymous_id, is_active=True).update(is_active=False)

        base_name = "Shopping List"
        i = 1
        while True:
            name = f"{base_name} #{i}"
            try:
                if user:
                    cart = Cart.objects.create(user=user, name=name, is_active=is_active)
                else:
                    # This part needs a unique constraint on (anonymous_id, name) to be robust
                    cart = Cart.objects.create(anonymous_id=anonymous_id, name=name, is_active=is_active)
                
                store_list = None
                if user:
                    store_list = SelectedStoreList.objects.filter(user=user).order_by('-last_used_at').first()
                elif anonymous_id:
                    store_list = SelectedStoreList.objects.filter(anonymous_id=anonymous_id).order_by('-last_used_at').first()

                if store_list:
                    cart.selected_store_list = store_list
                    cart.save()
                
                return cart
            except IntegrityError:
                i += 1

    def rename_cart(self, cart, new_name):
        cart.name = new_name
        cart.save()
        return cart

    def delete_cart(self, cart):
        cart.delete()