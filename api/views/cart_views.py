from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart, CartItem, CartSubstitution
from api.serializers import CartSerializer, CartItemSerializer, CartSubstitutionSerializer

class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id)
        return Cart.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            # Deactivate other carts for this user
            Cart.objects.filter(user=self.request.user, is_active=True).update(is_active=False)
            serializer.save(user=self.request.user, is_active=True)
        elif hasattr(self.request, 'anonymous_id'):
            # Deactivate other carts for this anonymous user
            Cart.objects.filter(anonymous_id=self.request.anonymous_id, is_active=True).update(is_active=False)
            serializer.save(anonymous_id=self.request.anonymous_id, is_active=True)
        else:
            raise permissions.PermissionDenied("Cannot create a cart without being authenticated or having an anonymous ID.")

class CartRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Cart.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id)
        return Cart.objects.none()

class ActiveCartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=self.request.user, is_active=True,
                defaults={'name': f"{self.request.user.email}'s Cart"}
            )
            return cart
        elif hasattr(self.request, 'anonymous_id'):
            cart, created = Cart.objects.get_or_create(
                anonymous_id=self.request.anonymous_id, is_active=True,
                defaults={'name': 'Anonymous Cart'}
            )
            return cart
        raise permissions.PermissionDenied("No active cart found.")

class SwitchActiveCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({'error': 'cart_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Deactivate current active cart
            Cart.objects.filter(user=request.user, is_active=True).update(is_active=False)
            # Activate new cart
            new_active_cart = Cart.objects.get(user=request.user, pk=cart_id)
            new_active_cart.is_active = True
            new_active_cart.save()
            return Response(CartSerializer(new_active_cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

# --- Views for items in the ACTIVE cart ---

class ActiveCartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_active_cart(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user, is_active=True).first()
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id, is_active=True).first()
        return None

    def get_queryset(self):
        cart = self.get_active_cart()
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

    def perform_create(self, serializer):
        cart = self.get_active_cart()
        if not cart:
            raise permissions.PermissionDenied("No active cart available.")
        serializer.save(cart=cart)

class ActiveCartItemUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(cart__user=self.request.user, cart__is_active=True)
        elif hasattr(self.request, 'anonymous_id'):
            return CartItem.objects.filter(cart__anonymous_id=self.request.anonymous_id, cart__is_active=True)
        return CartItem.objects.none()

