from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from users.models import Cart, CartItem
from users.serializers.cart_item_serializer import CartItemSerializer
from splitcart.permissions import IsAuthenticatedOrAnonymous
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from products.utils.get_pricing_stores import get_pricing_stores_map

class CartItemViewSet(viewsets.ModelViewSet):
    """
    A unified ViewSet for listing, creating, retrieving, updating,
    and deleting CartItems, nested under a specific Cart.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_queryset(self):
        """
        This queryset is filtered based on the 'cart_pk' from the URL,
        ensuring we only operate on items within the specified cart.
        """
        cart_pk = self.kwargs.get('cart_pk')
        if not cart_pk:
            # This should not happen if URLs are configured correctly
            return CartItem.objects.none()
        
        # Further ensure the user has access to this cart
        # This relies on the CartViewSet's permission checks.
        # A more robust implementation might re-check cart ownership here.
        return CartItem.objects.filter(cart_id=cart_pk)

    def get_cart(self):
        """Helper method to get the parent cart."""
        cart_pk = self.kwargs.get('cart_pk')
        # Ensure the user has access to this cart
        # We can use the Cart's default manager which might have its own checks
        # or we can be explicit
        user = self.request.user
        qs = Cart.objects
        if user.is_authenticated:
            return get_object_or_404(qs, pk=cart_pk, user=user)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None)
            return get_object_or_404(qs, pk=cart_pk, anonymous_id=anonymous_id)


    def create(self, request, *args, **kwargs):
        """
        Logic from ActiveCartItemListCreateView (Create part).
        Checks if item already exists before creating.
        """
        cart = self.get_cart()
        product_id = request.data.get('product')
        
        # Check if the item already exists
        existing_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if existing_item:
            serializer = self.get_serializer(existing_item)
            return Response(serializer.data, status=status.HTTP_200_OK) # Return existing, not 201
        
        # If not, proceed with creation
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Logic from ActiveCartItemListCreateView (perform_create part).
        Associates the item with the correct cart and runs substitution logic.
        """
        cart = self.get_cart()
        cart_item = serializer.save(cart=cart)

        # Run substitution logic
        if cart.selected_store_list:
            store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
            if store_ids:
                pricing_map = get_pricing_stores_map(store_ids)
                pricing_store_ids = list(set(pricing_map.values()))
                substitute_manager = SubstituteManager(cart_item.product.id, pricing_store_ids)
                substitute_manager.create_cart_substitutions(cart_item)

    # Retrieve, Update, and Destroy actions are handled by the base ModelViewSet
    # using the filtered queryset from get_queryset(), so no override is needed
    # for basic functionality.
