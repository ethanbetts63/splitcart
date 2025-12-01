from rest_framework import generics, status
from api.permissions import IsAuthenticatedOrAnonymous
from rest_framework.response import Response
from users.models import CartItem
from products.models import Product
from api.serializers import CartItemSerializer
from users.cart_manager import CartManager
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from api.utils.get_pricing_stores import get_pricing_stores_map

cart_manager = CartManager()

class ActiveCartItemListCreateView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def create(self, request, *args, **kwargs):
        cart = cart_manager.get_active_cart(self.request)
        if not cart:
            return Response({"detail": "No active cart available."}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get('product')
        product = Product.objects.filter(pk=product_id).first()

        if not product:
            return Response({"detail": "Invalid product ID."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if cart_item:
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        cart = cart_manager.get_active_cart(self.request)
        cart_item = serializer.save(cart=cart)

        if cart.selected_store_list:
            store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
            if store_ids:
                # Use the helper to determine the correct stores for price lookups
                pricing_map = get_pricing_stores_map(store_ids)
                pricing_store_ids = list(set(pricing_map.values()))
                print(f"Initializing SubstituteManager for product: {cart_item.product.id}")
                substitute_manager = SubstituteManager(cart_item.product.id, pricing_store_ids)
                substitute_manager.create_cart_substitutions(cart_item)
        else:
            print("No selected_store_list found on cart, skipping substitution search.")
