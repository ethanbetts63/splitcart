from django.db import IntegrityError
from rest_framework import generics, permissions, status
from api.permissions import IsAuthenticatedOrAnonymous
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart, CartItem
from products.models import Product
from api.serializers import CartSerializer, CartItemSerializer
from users.cart_manager import CartManager
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager

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

class ActiveCartDetailView(APIView):
    permission_classes = [IsAuthenticatedOrAnonymous]

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
        except IntegrityError:
            return Response({'error': 'A cart with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)

# --- Views for items in the ACTIVE cart ---

class ActiveCartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

    def create(self, request, *args, **kwargs):
        cart = cart_manager.get_active_cart(self.request)
        if not cart:
            return Response({"detail": "No active cart available."}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get('product')
        # Using .get() to avoid an exception if the product doesn't exist, though the serializer would catch it.
        product = Product.objects.filter(pk=product_id).first()

        if not product:
            return Response({"detail": "Invalid product ID."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if item exists
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if cart_item:
            # Item exists, just serialize and return it gracefully.
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Item does not exist, proceed with standard creation logic from the parent class.
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        cart = cart_manager.get_active_cart(self.request)
        cart_item = serializer.save(cart=cart)

        # Automatically find and create unapproved CartSubstitution instances
        if cart.selected_store_list:
            store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
            if store_ids:
                substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
                substitute_manager.create_cart_substitutions(cart_item)


from users.models import Cart, CartItem, CartSubstitution
from products.models import Product
from api.serializers import CartSerializer, CartItemSerializer, CartSubstitutionSerializer
from users.cart_manager import CartManager
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager

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

class ActiveCartDetailView(APIView):
    permission_classes = [IsAuthenticatedOrAnonymous]

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
        except IntegrityError:
            return Response({'error': 'A cart with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)

# --- Views for items in the ACTIVE cart ---

class ActiveCartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

    def create(self, request, *args, **kwargs):
        cart = cart_manager.get_active_cart(self.request)
        if not cart:
            return Response({"detail": "No active cart available."}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get('product')
        # Using .get() to avoid an exception if the product doesn't exist, though the serializer would catch it.
        product = Product.objects.filter(pk=product_id).first()

        if not product:
            return Response({"detail": "Invalid product ID."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if item exists
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if cart_item:
            # Item exists, just serialize and return it gracefully.
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Item does not exist, proceed with standard creation logic from the parent class.
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        cart = cart_manager.get_active_cart(self.request)
        cart_item = serializer.save(cart=cart)

        # Automatically find and create unapproved CartSubstitution instances
        if cart.selected_store_list:
            store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
            if store_ids:
                substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
                substitute_manager.create_cart_substitutions(cart_item)


class ActiveCartItemUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    lookup_field = 'pk'

    def get_queryset(self):
        cart = cart_manager.get_active_cart(self.request)
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()


class CartSubstitutionUpdateDestroyView(APIView):
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_cart_item(self, cart_item_pk):
        cart = cart_manager.get_active_cart(self.request)
        if not cart:
            return None
        try:
            return CartItem.objects.get(pk=cart_item_pk, cart=cart)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, cart_item_pk, substitution_pk, *args, **kwargs):
        cart_item = self.get_cart_item(cart_item_pk)
        if not cart_item:
            return Response({"detail": "CartItem not found or does not belong to active cart."}, status=status.HTTP_404_NOT_FOUND)

        is_approved = request.data.get('is_approved')
        quantity = request.data.get('quantity')

        # Ensure at least one field is provided for update
        if is_approved is None and quantity is None:
            return Response({"detail": "At least 'is_approved' or 'quantity' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve store_ids for SubstituteManager (required by its __init__)
        store_ids = []
        if cart_item.cart.selected_store_list:
            store_ids = list(cart_item.cart.selected_store_list.stores.values_list('id', flat=True))
        
        if not store_ids:
            # This case should ideally not happen if cart_item was created with store_ids
            # but we need to handle the SubstituteManager's ValueError
            return Response({"detail": "No stores associated with the cart to manage substitutions."}, status=status.HTTP_400_BAD_REQUEST)

        substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
        updated_sub = substitute_manager.update_cart_substitution(str(substitution_pk), is_approved=is_approved, quantity=quantity)

        if updated_sub is None:
            return Response({"detail": "CartSubstitution not found or removed due to quantity 0."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CartSubstitutionSerializer(updated_sub)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, cart_item_pk, substitution_pk, *args, **kwargs):
        cart_item = self.get_cart_item(cart_item_pk)
        if not cart_item:
            return Response({"detail": "CartItem not found or does not belong to active cart."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve store_ids for SubstituteManager (required by its __init__)
        store_ids = []
        if cart_item.cart.selected_store_list:
            store_ids = list(cart_item.cart.selected_store_list.stores.values_list('id', flat=True))
        
        if not store_ids:
            return Response({"detail": "No stores associated with the cart to manage substitutions."}, status=status.HTTP_400_BAD_REQUEST)

        substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
        removed = substitute_manager.remove_cart_substitution(str(substitution_pk))

        if removed:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "CartSubstitution not found."}, status=status.HTTP_404_NOT_FOUND)

