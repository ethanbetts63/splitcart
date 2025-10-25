from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart
from api.serializers import CartSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

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
