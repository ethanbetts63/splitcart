from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from splitcart.permissions import IsAuthenticatedOrAnonymous
from users.models import Cart, CartItem
from products.models import Product
from data_management.utils.cart_optimization.substitute_manager import SubstituteManager
from users.serializers.cart_serializer import CartSerializer

class CartSyncView(APIView):
    """
    API view to synchronize the entire state of a cart from the client.
    Accepts a POST request with a list of all items in the cart.
    """
    permission_classes = [IsAuthenticatedOrAnonymous]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # 1. Data Validation
            cart_id = request.data.get('cart_id')
            items_data = request.data.get('items')

            if not cart_id:
                raise ValidationError({'cart_id': 'Cart ID is required.'})
            if not isinstance(items_data, list):
                raise ValidationError({'items': 'Items must be a list.'})

            try:
                cart = Cart.objects.select_related('selected_store_list').prefetch_related('selected_store_list__stores').get(id=cart_id)
            except Cart.DoesNotExist:
                raise ValidationError({'cart_id': 'Cart not found.'})

            # Ensure user owns the cart or is anonymous owner
            if request.user.is_authenticated and cart.user != request.user:
                raise ValidationError({'cart_id': 'Cart does not belong to the authenticated user.'})
            elif not request.user.is_authenticated and cart.anonymous_id != getattr(request, 'anonymous_id', None):
                raise ValidationError({'cart_id': 'Cart does not belong to the anonymous user.'})

            # 2. Fetch Existing State
            existing_cart_items = CartItem.objects.filter(cart=cart).select_related('product')
            existing_items_map = {item.product.id: item for item in existing_cart_items}

            # 3. Reconciliation Logic
            to_create = []
            to_update = []
            incoming_product_ids = set()

            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')

                if not product_id or not isinstance(product_id, int):
                    raise ValidationError({'items': 'Each item must have a valid product_id.'})
                if not isinstance(quantity, int) or quantity <= 0:
                    raise ValidationError({'items': 'Each item must have a quantity greater than 0.'})

                incoming_product_ids.add(product_id)

                if product_id in existing_items_map:
                    # Item exists, check for quantity update
                    existing_item = existing_items_map[product_id]
                    if existing_item.quantity != quantity:
                        existing_item.quantity = quantity
                        to_update.append(existing_item)
                else:
                    # Item is new, prepare for creation
                    try:
                        product = Product.objects.get(id=product_id)
                    except Product.DoesNotExist:
                        raise ValidationError({'items': f'Product with ID {product_id} not found.'})
                    to_create.append(CartItem(cart=cart, product=product, quantity=quantity))

            # Items to delete (exist in DB but not in incoming data)
            to_delete_ids = [ 
                item.id for product_id, item in existing_items_map.items()
                if product_id not in incoming_product_ids
            ]

            # 4. Perform Bulk Database Operations
            if to_delete_ids:
                CartItem.objects.filter(id__in=to_delete_ids).delete()

            if to_update:
                CartItem.objects.bulk_update(to_update, ['quantity'])

            if to_create:
                # Bulk create returns the created objects, which we need for substitutions
                created_items = CartItem.objects.bulk_create(to_create)
                # 5. Handle Substitutions for newly created items
                store_ids = []
                if cart.selected_store_list:
                    store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))

                if store_ids:
                    for item in created_items:
                        manager = SubstituteManager(product_id=item.product.id, store_ids=store_ids)
                        manager.create_cart_substitutions(original_cart_item=item)
                else:
                    print(f"Skipping substitution creation for cart {cart.id} due to missing store_ids.")

        # Re-fetch the cart to get the latest state including substitutions
        # and return it to the frontend.
        cart.refresh_from_db() # Ensure cart object is up-to-date after transaction
        serializer = CartSerializer(cart) # Use CartSerializer for response

        return Response(serializer.data, status=status.HTTP_200_OK)
