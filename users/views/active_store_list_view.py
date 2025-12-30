from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from splitcart.permissions import IsAuthenticatedOrAnonymous
from users.models import SelectedStoreList
from users.serializers import SelectedStoreListSerializer
from products.utils.get_pricing_stores import get_pricing_stores_map


class ActiveStoreListView(APIView):
    """
    View to get the active (most recently used) store list for a user.
    Handles both authenticated and anonymous users.
    """
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get(self, request, *args, **kwargs):
        user = request.user
        anonymous_id = getattr(request, 'anonymous_id', None)
        store_list = None

        if user.is_authenticated:
            store_list = SelectedStoreList.objects.filter(user=user).order_by('-last_used_at').first()
        elif anonymous_id:
            store_list = SelectedStoreList.objects.filter(anonymous_id=anonymous_id).order_by('-last_used_at').first()

        if not store_list:
            return Response({"detail": "No active store list found."}, status=status.HTTP_404_NOT_FOUND)

        store_ids = list(store_list.stores.values_list('id', flat=True))
        anchor_map = get_pricing_stores_map(store_ids)
        
        serializer = SelectedStoreListSerializer(store_list)

        response_data = {
            'store_list': serializer.data,
            'anchor_map': anchor_map,
        }

        return Response(response_data, status=status.HTTP_200_OK)
