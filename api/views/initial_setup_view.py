import uuid
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart, SelectedStoreList
from api.serializers import CartSerializer, SelectedStoreListSerializer
from api.permissions import IsAuthenticatedOrAnonymous

from products.models import Price

class InitialSetupView(APIView):
    permission_classes = [IsAuthenticatedOrAnonymous]

    def post(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        anonymous_id = getattr(request, 'anonymous_id', None)

        # If user is not authenticated and no anonymous ID is present, create one.
        if not user and not anonymous_id:
            anonymous_id = uuid.uuid4()

        # Get or create the store list
        store_list = None
        if user:
            store_list = SelectedStoreList.objects.filter(user=user).order_by('-last_used_at').first()
        elif anonymous_id:
            store_list = SelectedStoreList.objects.filter(anonymous_id=anonymous_id).order_by('-last_used_at').first()

        if not store_list:
            if user:
                store_list = SelectedStoreList.objects.create(user=user, name='Default List')
            elif anonymous_id:
                store_list = SelectedStoreList.objects.create(anonymous_id=anonymous_id, name='Default List')

        # Get or create the active cart
        cart_filter = {'user': user, 'is_active': True} if user else {'anonymous_id': anonymous_id, 'is_active': True}
        cart_defaults = {'name': f"{user.email}'s Cart"} if user and user.email else {'name': 'Anonymous Cart'}
        cart, _ = Cart.objects.get_or_create(
            **cart_filter,
            defaults=cart_defaults
        )

        # Link the store list to the cart if it's not already linked
        if not cart.selected_store_list:
            cart.selected_store_list = store_list
            cart.save()

        # --- OPTIMIZATION --- #
        # 1. Get all product and store IDs for the query
        product_ids = [item.product_id for item in cart.items.all()]
        store_ids = []
        if cart.selected_store_list:
            store_ids = cart.selected_store_list.stores.values_list('id', flat=True)

        # 2. Fetch all relevant, pre-filtered prices in a single query
        prices_queryset = Price.objects.filter(
            price_record__product_id__in=product_ids,
            store_id__in=store_ids
        ).select_related('store__company', 'price_record')

        # 3. Group prices by product ID for efficient lookup in the serializer
        prices_map = {}
        for price in prices_queryset:
            product_id = price.price_record.product_id
            if product_id not in prices_map:
                prices_map[product_id] = []
            prices_map[product_id].append(price)

        # 4. Pass the pre-filtered data to the serializer via context
        serializer_context = {
            'prices_map': prices_map,
            'nearby_store_ids': store_ids # Pass for consistency, though filtering is done
        }
        cart_serializer = CartSerializer(cart, context=serializer_context)

        response_data = {
            'cart': cart_serializer.data,
        }
        if anonymous_id:
            response_data['anonymous_id'] = anonymous_id

        return Response(response_data, status=status.HTTP_200_OK)
