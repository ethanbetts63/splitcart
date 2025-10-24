from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart, CartItem
from api.serializers import CartSerializer, CartItemSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

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
        name = serializer.validated_data.get('name', 'New Cart')
        cart = cart_manager.create_cart(self.request, name)
        if not cart:
            raise permissions.PermissionDenied("Cannot create a cart without being authenticated or having an anonymous ID.")
        serializer.instance = cart

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

    def perform_destroy(self, instance):
        cart_manager.delete_cart(instance)

class ActiveCartDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        cart = cart_manager.get_active_cart(request)
        if cart:
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        return Response({"detail": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)

class SwitchActiveCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({'error': 'cart_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_active_cart = cart_manager.switch_active_cart(request.user, cart_id)
            return Response(CartSerializer(new_active_cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

class RenameCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart_id = request.data.get('cart_id')
        new_name = request.data.get('new_name')
        if not cart_id or not new_name:
            return Response({'error': 'cart_id and new_name are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user=request.user, pk=cart_id)
            cart_manager.rename_cart(cart, new_name)
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

# --- Views for items in the ACTIVE cart ---

class ActiveCartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

    def perform_create(self, serializer):
        cart = cart_manager.get_active_cart(self.request)
        if not cart:
            raise permissions.PermissionDenied("No active cart available.")
        serializer.save(cart=cart)

class ActiveCartItemUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

