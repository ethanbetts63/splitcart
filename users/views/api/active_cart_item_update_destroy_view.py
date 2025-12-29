from rest_framework import generics
from api.permissions import IsAuthenticatedOrAnonymous
from users.models import CartItem
from users.serializers.api import CartItemSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

class ActiveCartItemUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    lookup_field = 'pk'

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()
