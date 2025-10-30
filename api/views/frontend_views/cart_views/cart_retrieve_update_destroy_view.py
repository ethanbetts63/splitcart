from rest_framework import generics
from api.permissions import IsAuthenticatedOrAnonymous
from users.models import Cart
from api.serializers import CartSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

class CartRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    queryset = Cart.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id)
        return Cart.objects.none()

    def perform_destroy(self, instance):
        cart_manager.delete_cart(instance)
