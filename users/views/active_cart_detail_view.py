from rest_framework import status
from api.permissions import IsAuthenticatedOrAnonymous
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers.api import CartSerializer
from users.cart_manager import CartManager

cart_manager = CartManager()

class ActiveCartDetailView(APIView):
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get(self, request, *args, **kwargs):
        cart = cart_manager.get_active_cart(request)
        if cart:
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        return Response({"detail": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)
