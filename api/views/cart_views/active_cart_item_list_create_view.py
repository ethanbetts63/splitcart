from rest_framework import generics, status
from api.permissions import IsAuthenticatedOrAnonymous
from rest_framework.response import Response
from users.models import CartItem
from products.models import Product
from api.serializers import CartItemSerializer
from users.cart_manager import CartManager
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager

cart_manager = CartManager()

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
        print("--- ActiveCartItemListCreateView: perform_create called ---")
        cart = cart_manager.get_active_cart(self.request)
        cart_item = serializer.save(cart=cart)
        print(f"Created CartItem: {cart_item}")

        if cart.selected_store_list:
            store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
            print(f"Found store_ids for substitution search: {store_ids}")
            if store_ids:
                print(f"Initializing SubstituteManager for product: {cart_item.product.id}")
                substitute_manager = SubstituteManager(cart_item.product.id, store_ids)
                substitute_manager.create_cart_substitutions(cart_item)
                print("Finished create_cart_substitutions call.")
        else:
            print("No selected_store_list found on cart, skipping substitution search.")
