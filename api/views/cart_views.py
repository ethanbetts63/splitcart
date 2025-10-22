from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from users.models import Cart, CartItem, CartSubstitution
from api.serializers import CartSerializer, CartItemSerializer, CartSubstitutionSerializer

class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        # For anonymous users, we'll need to get anonymous_id from cookie/header
        return Cart.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            # For anonymous users, save with anonymous_id
            pass

class CartRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Cart.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        # For anonymous users, we'll need to get anonymous_id from cookie/header
        return Cart.objects.none()

class CartItemCreateView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        cart_pk = self.kwargs.get('cart_pk')
        try:
            cart = Cart.objects.get(pk=cart_pk)
            # Ensure the cart belongs to the user
            if self.request.user.is_authenticated and cart.user != self.request.user:
                raise permissions.PermissionDenied("You do not have permission to add items to this cart.")
            # Add anonymous_id check later
            serializer.save(cart=cart)
        except Cart.DoesNotExist:
            raise generics.ValidationError("Cart not found.")

class CartItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = CartItem.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        cart_pk = self.kwargs.get('cart_pk')
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(cart__pk=cart_pk, cart__user=self.request.user)
        # Add anonymous_id check later
        return CartItem.objects.none()

class CartSubstitutionCreateView(generics.CreateAPIView):
    serializer_class = CartSubstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        cart_item_pk = self.kwargs.get('cart_item_pk')
        try:
            cart_item = CartItem.objects.get(pk=cart_item_pk)
            # Ensure the cart_item belongs to the user's cart
            if self.request.user.is_authenticated and cart_item.cart.user != self.request.user:
                raise permissions.PermissionDenied("You do not have permission to add substitutions to this cart item.")
            # Add anonymous_id check later
            serializer.save(original_cart_item=cart_item)
        except CartItem.DoesNotExist:
            raise generics.ValidationError("Cart item not found.")

class CartSubstitutionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSubstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = CartSubstitution.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        cart_item_pk = self.kwargs.get('cart_item_pk')
        if self.request.user.is_authenticated:
            return CartSubstitution.objects.filter(original_cart_item__pk=cart_item_pk, original_cart_item__cart__user=self.request.user)
        # Add anonymous_id check later
        return CartSubstitution.objects.none()
