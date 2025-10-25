import uuid
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Cart, SelectedStoreList
from api.serializers import CartSerializer, SelectedStoreListSerializer
from api.permissions import IsAuthenticatedOrAnonymous

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
        cart_defaults = {'name': f"{user.email}'s Cart"} if user else {'name': 'Anonymous Cart'}
        cart, _ = Cart.objects.get_or_create(
            **cart_filter,
            defaults=cart_defaults
        )

        # Link the store list to the cart if it's not already linked
        if not cart.selected_store_list:
            cart.selected_store_list = store_list
            cart.save()

        # Serialize and return the data
        cart_serializer = CartSerializer(cart)
        store_list_serializer = SelectedStoreListSerializer(store_list)

        response_data = {
            'cart': cart_serializer.data,
            'store_list': store_list_serializer.data
        }
        if anonymous_id:
            response_data['anonymous_id'] = anonymous_id

        return Response(response_data, status=status.HTTP_200_OK)
