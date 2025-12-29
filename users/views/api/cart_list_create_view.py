from rest_framework import generics, permissions
from api.permissions import IsAuthenticatedOrAnonymous
from users.models import Cart
from users.serializers.api import CartSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id)
        return Cart.objects.none()

    def perform_create(self, serializer):
        cart = cart_manager.create_cart(self.request)
        if not cart:
            raise permissions.PermissionDenied("Cannot create a cart without being authenticated or having an anonymous ID.")
        serializer.instance = cart
