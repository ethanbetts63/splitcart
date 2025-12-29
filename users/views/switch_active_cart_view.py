from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart
from users.serializers.cart_serializer import CartSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

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
