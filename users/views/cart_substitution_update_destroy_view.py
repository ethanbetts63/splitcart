from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import CartItem
from users.serializers.cart_substitution_serializer import CartSubstitutionSerializer
from users.cart_manager import CartManager
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from splitcart.permissions import IsAuthenticatedOrAnonymous

cart_manager = CartManager()

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

        if is_approved is None and quantity is None:
            return Response({"detail": "At least 'is_approved' or 'quantity' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        store_ids = []
        if cart_item.cart.selected_store_list:
            store_ids = list(cart_item.cart.selected_store_list.stores.values_list('id', flat=True))
        
        if not store_ids:
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
