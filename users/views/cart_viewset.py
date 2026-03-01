from django.db import IntegrityError, transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from users.models import Cart, CartItem, CartSubstitution, SelectedStoreList
from products.models import Product
from users.serializers.cart_serializer import CartSerializer
from splitcart.permissions import IsAuthenticatedOrAnonymous
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from users.utils.name_generator import generate_unique_name
from users.utils.cart_optimization import run_cart_optimization


class CartViewSet(viewsets.ModelViewSet):
    """
    A unified ViewSet for listing, creating, retrieving, updating,
    and deleting Carts. Also includes custom actions for specific
    cart-related operations. All business logic is contained within this ViewSet.
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
        Creates a new cart and deactivates any existing active carts for the user.
        Associates the new cart with the most recent store list.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        anonymous_id = getattr(self.request, 'anonymous_id', None)

        if not user and not anonymous_id:
            raise permissions.PermissionDenied("Cannot create a cart without being authenticated or having an anonymous ID.")

        # Deactivate other active carts
        if user:
            Cart.objects.filter(user=user, is_active=True).update(is_active=False)
        elif anonymous_id:
            Cart.objects.filter(anonymous_id=anonymous_id, is_active=True).update(is_active=False)

        owner_filter = {'user': user} if user else {'anonymous_id': anonymous_id}
        unique_name = generate_unique_name(Cart, owner_filter, "Shopping List")
        
        # is_active is True by default for new carts via this method
        cart = serializer.save(**owner_filter, name=unique_name, is_active=True)
        
        # Associate with the most recent store list
        store_list_owner_filter = {'user': user} if user else {'anonymous_id': anonymous_id}
        store_list = SelectedStoreList.objects.filter(**store_list_owner_filter).order_by('-last_used_at').first()
        if store_list:
            cart.selected_store_list = store_list
            cart.save()

    def perform_destroy(self, instance):
        """
        Deletes the cart instance.
        """
        instance.delete()

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request, *args, **kwargs):
        """
        Retrieves the currently active cart for the user. If one does not exist,
        it creates one.
        """
        cart = None
        created = False
        user = request.user
        
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=user, is_active=True,
                defaults={'name': f"{user.email}'s Cart"}
            )
        elif hasattr(request, 'anonymous_id'):
            cart, created = Cart.objects.get_or_create(
                anonymous_id=request.anonymous_id, is_active=True,
                defaults={'name': 'Anonymous Cart'}
            )
        else:
             return Response({"detail": "Authentication or anonymous ID required."}, status=status.HTTP_403_FORBIDDEN)

        if created:
            store_list = None
            if user.is_authenticated:
                store_list = SelectedStoreList.objects.filter(user=user).order_by('-last_used_at').first()
            elif hasattr(request, 'anonymous_id'):
                store_list = SelectedStoreList.objects.filter(anonymous_id=request.anonymous_id).order_by('-last_used_at').first()
            
            if store_list:
                cart.selected_store_list = store_list
                cart.save()

        if cart:
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        return Response({"detail": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='rename', permission_classes=[permissions.IsAuthenticated])
    def rename(self, request, *args, **kwargs):
        """
        Renames a specific cart.
        """
        cart_id = request.data.get('cart_id')
        new_name = request.data.get('new_name')
        if not cart_id or not new_name:
            return Response({'error': 'cart_id and new_name are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = self.get_queryset().get(pk=cart_id)
            cart.name = new_name
            cart.save()
            return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'A cart with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='switch-active', permission_classes=[permissions.IsAuthenticated])
    def switch_active(self, request, *args, **kwargs):
        """
        Sets a specific cart as the active one for the user.
        """
        cart_id = request.data.get('cart_id')
        user = request.user
        if not cart_id:
            return Response({'error': 'cart_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Cart.objects.filter(user=user, is_active=True).update(is_active=False)
                new_active_cart = self.get_queryset().get(pk=cart_id)
                new_active_cart.is_active = True
                new_active_cart.save()
            return Response(self.get_serializer(new_active_cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request, *args, **kwargs):
        """
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
                cart = self.get_queryset().get(id=cart_id)
            except Cart.DoesNotExist:
                raise ValidationError({'cart_id': 'Cart not found.'})

            # Lazy-link the store list if the cart doesn't have one yet.
            # The store list is saved independently by the frontend; it just may not
            # have been linked when the cart was first created.
            if not cart.selected_store_list:
                user = request.user
                owner_filter = {'user': user} if user.is_authenticated else {'anonymous_id': getattr(request, 'anonymous_id', None)}
                if any(v is not None for v in owner_filter.values()):
                    store_list = SelectedStoreList.objects.filter(**owner_filter).order_by('-last_used_at').first()
                    if store_list:
                        cart.selected_store_list = store_list
                        cart.save(update_fields=['selected_store_list'])

            existing_items_map = {item.product.id: item for item in cart.items.select_related('product')}
            incoming_product_ids = {item_data.get('product_id') for item_data in items_data}

            to_delete_ids = [
                item.id for product_id, item in existing_items_map.items()
                if product_id not in incoming_product_ids
            ]
            if to_delete_ids:
                CartItem.objects.filter(id__in=to_delete_ids).delete()

            to_create = []
            to_update = []
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')

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

            # Process substitution approval state sent from the client.
            # Build a map of product_id -> substitutions data for efficient lookup.
            subs_by_product = {
                item_data.get('product_id'): item_data.get('substitutions', [])
                for item_data in items_data
                if item_data.get('substitutions')
            }
            if subs_by_product:
                current_items_map = {item.product.id: item for item in cart.items.select_related('product')}
                subs_to_update = []
                for product_id, substitutions_data in subs_by_product.items():
                    cart_item = current_items_map.get(product_id)
                    if not cart_item:
                        continue
                    sub_ids = [s.get('id') for s in substitutions_data if s.get('id')]
                    existing_subs = {str(s.id): s for s in CartSubstitution.objects.filter(
                        original_cart_item=cart_item, id__in=sub_ids
                    )}
                    for sub_data in substitutions_data:
                        sub = existing_subs.get(str(sub_data.get('id')))
                        if sub is None:
                            continue
                        sub.is_approved = sub_data.get('is_approved', sub.is_approved)
                        sub.quantity = sub_data.get('quantity', sub.quantity)
                        subs_to_update.append(sub)
                if subs_to_update:
                    CartSubstitution.objects.bulk_update(subs_to_update, ['is_approved', 'quantity'])

            if to_create:
                created_items = CartItem.objects.bulk_create(to_create)
                if cart.selected_store_list:
                    store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
                    if store_ids:
                        for item in created_items:
                            manager = SubstituteManager(product_id=item.product.id, store_ids=store_ids)
                            manager.create_cart_substitutions(original_cart_item=item)

        cart = Cart.objects.prefetch_related(
            'items__product__prices__store__company',
            'items__product__category__primary_category',
            'items__product__skus__company',
            'items__chosen_substitutions__substituted_product__prices__store__company',
            'items__chosen_substitutions__substituted_product__category__primary_category',
            'items__chosen_substitutions__substituted_product__skus__company',
        ).get(pk=cart.pk)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='optimize')
    def optimize(self, request, *args, **kwargs):
        """
        Performs optimization on a specific cart by calling the optimization utility.
        The store list for optimization is passed directly in the request body.
        """
        cart_obj = self.get_object()
        store_list = cart_obj.selected_store_list
        if not store_list:
            return Response({'error': 'No store list linked to this cart.'}, status=status.HTTP_400_BAD_REQUEST)

        max_stores_options = request.data.get('max_stores_options', [2, 3, 4])
        return run_cart_optimization(cart_obj, store_list, max_stores_options)
