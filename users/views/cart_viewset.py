from django.db import IntegrityError, transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from users.models import Cart, CartItem
from products.models import Product
from users.serializers.cart_serializer import CartSerializer
from users.cart_manager import CartManager
from splitcart.permissions import IsAuthenticatedOrAnonymous
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager

# It's good practice to instantiate managers once if they are stateless
cart_manager = CartManager()

class CartViewSet(viewsets.ModelViewSet):
    """
    A unified ViewSet for listing, creating, retrieving, updating,
    and deleting Carts. Also includes custom actions for specific
    cart-related operations.
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    lookup_field = 'pk'

    def get_queryset(self):
        """
        This queryset is the base for all retrieval operations.
        It ensures that users can only access their own carts.
        """
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            return Cart.objects.filter(anonymous_id=self.request.anonymous_id)
        return Cart.objects.none()

    def perform_create(self, serializer):
        """
        Logic from CartListCreateView.
        Delegates cart creation to the CartManager.
        """
        cart = cart_manager.create_cart(self.request)
        if not cart:
            raise permissions.PermissionDenied("Cannot create a cart without being authenticated or having an anonymous ID.")
        serializer.instance = cart

    def perform_destroy(self, instance):
        """
        Logic from CartRetrieveUpdateDestroyView.
        Delegates cart deletion to the CartManager.
        """
        cart_manager.delete_cart(instance)

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request, *args, **kwargs):
        """
        Logic from ActiveCartDetailView.
        Retrieves the currently active cart for the user.
        """
        cart = cart_manager.get_active_cart(request)
        if cart:
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        return Response({"detail": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='rename', permission_classes=[permissions.IsAuthenticated])
    def rename(self, request, *args, **kwargs):
        """
        Logic from RenameCartView.
        Renames a specific cart.
        """
        cart_id = request.data.get('cart_id')
        new_name = request.data.get('new_name')
        if not cart_id or not new_name:
            return Response({'error': 'cart_id and new_name are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use the viewset's queryset to ensure permission checking
            cart = self.get_queryset().get(pk=cart_id)
            cart_manager.rename_cart(cart, new_name)
            return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'A cart with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='switch-active', permission_classes=[permissions.IsAuthenticated])
    def switch_active(self, request, *args, **kwargs):
        """
        Logic from SwitchActiveCartView.
        Sets a specific cart as the active one for the user.
        """
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({'error': 'cart_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_active_cart = cart_manager.switch_active_cart(request.user, cart_id)
            return Response(self.get_serializer(new_active_cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request, *args, **kwargs):
        """
        Logic from CartSyncView.
        Synchronizes the entire state of a cart from the client.
        """
        with transaction.atomic():
            cart_id = request.data.get('cart_id')
            items_data = request.data.get('items')

            if not cart_id:
                raise ValidationError({'cart_id': 'Cart ID is required.'})
            if not isinstance(items_data, list):
                raise ValidationError({'items': 'Items must be a list.'})

            try:
                # Use the viewset's queryset to ensure the user owns the cart
                cart = self.get_queryset().get(id=cart_id)
            except Cart.DoesNotExist:
                raise ValidationError({'cart_id': 'Cart not found.'})

            existing_items_map = {item.product.id: item for item in cart.items.select_related('product')}
            incoming_product_ids = {item_data.get('product_id') for item_data in items_data}

            # 1. Items to Delete
            to_delete_ids = [
                item.id for product_id, item in existing_items_map.items()
                if product_id not in incoming_product_ids
            ]
            if to_delete_ids:
                CartItem.objects.filter(id__in=to_delete_ids).delete()

            # 2. Items to Create or Update
            to_create = []
            to_update = []
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')

                # Basic validation for each item
                if not (product_id and isinstance(product_id, int) and isinstance(quantity, int) and quantity > 0):
                    raise ValidationError({'items': f'Invalid data for item: {item_data}'})

                if product_id in existing_items_map:
                    existing_item = existing_items_map[product_id]
                    if existing_item.quantity != quantity:
                        existing_item.quantity = quantity
                        to_update.append(existing_item)
                else:
                    try:
                        product = Product.objects.get(id=product_id)
                        to_create.append(CartItem(cart=cart, product=product, quantity=quantity))
                    except Product.DoesNotExist:
                        raise ValidationError({'items': f'Product with ID {product_id} not found.'})

            if to_update:
                CartItem.objects.bulk_update(to_update, ['quantity'])

            if to_create:
                created_items = CartItem.objects.bulk_create(to_create)
                # Handle substitutions for newly created items
                if cart.selected_store_list:
                    store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
                    if store_ids:
                        for item in created_items:
                            manager = SubstituteManager(product_id=item.product.id, store_ids=store_ids)
                            manager.create_cart_substitutions(original_cart_item=item)

        cart.refresh_from_db()
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
