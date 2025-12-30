from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.models import CartItem
from users.serializers.cart_substitution_serializer import CartSubstitutionSerializer
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from splitcart.permissions import IsAuthenticatedOrAnonymous
from users.models import CartSubstitution


class CartSubstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = CartSubstitutionSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    lookup_field = 'pk'

    def get_queryset(self):
        # The parent CartItem's primary key is passed via the URL (e.g., /carts/{cart_pk}/items/{item_pk}/substitutions/)
        item_pk = self.kwargs.get('item_pk')
        if item_pk is None:
            return CartSubstitution.objects.none()
        
        # Ensure the CartItem belongs to the user's carts (either authenticated or anonymous)
        if self.request.user.is_authenticated:
            cart_items = CartItem.objects.filter(cart__user=self.request.user, pk=item_pk)
        elif hasattr(self.request, 'anonymous_id'):
            cart_items = CartItem.objects.filter(cart__anonymous_id=self.request.anonymous_id, pk=item_pk)
        else:
            return CartSubstitution.objects.none()

        if not cart_items.exists():
            return CartSubstitution.objects.none()
        
        cart_item = cart_items.first()
        return CartSubstitution.objects.filter(original_cart_item=cart_item)

    def get_cart_item_object(self):
        item_pk = self.kwargs.get('item_pk')
        if self.request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, pk=item_pk, cart__user=self.request.user)
        elif hasattr(self.request, 'anonymous_id'):
            cart_item = get_object_or_404(CartItem, pk=item_pk, cart__anonymous_id=self.request.anonymous_id)
        else:
            self.permission_denied(self.request)
        return cart_item

    def update(self, request, *args, **kwargs):
        substitution_pk = kwargs.get('pk')
        is_approved = request.data.get('is_approved')
        quantity = request.data.get('quantity')

        if is_approved is None and quantity is None:
            return Response({"detail": "At least 'is_approved' or 'quantity' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = self.get_cart_item_object()
        
        store_ids = []
        if cart_item.cart.selected_store_list:
            store_ids = list(cart_item.cart.selected_store_list.stores.values_list('id', flat=True))
        
        if not store_ids:
            return Response({"detail": "No stores associated with the cart to manage substitutions."}, status=status.HTTP_400_BAD_REQUEST)

        substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
        
        # substitute_manager.update_cart_substitution expects substitution_id as a string
        updated_sub = substitute_manager.update_cart_substitution(str(substitution_pk), is_approved=is_approved, quantity=quantity)

        if updated_sub is None:
            return Response({"detail": "CartSubstitution not found or removed due to quantity 0."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(updated_sub)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        substitution_pk = kwargs.get('pk')

        cart_item = self.get_cart_item_object()

        store_ids = []
        if cart_item.cart.selected_store_list:
            store_ids = list(cart_item.cart.selected_store_list.stores.values_list('id', flat=True))
        
        if not store_ids:
            return Response({"detail": "No stores associated with the cart to manage substitutions."}, status=status.HTTP_400_BAD_REQUEST)

        substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
        
        # substitute_manager.remove_cart_substitution expects substitution_id as a string
        removed = substitute_manager.remove_cart_substitution(str(substitution_pk))

        if removed:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "CartSubstitution not found."}, status=status.HTTP_404_NOT_FOUND)
