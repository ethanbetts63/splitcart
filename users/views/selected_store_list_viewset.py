from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from users.models import SelectedStoreList
from users.serializers import SelectedStoreListSerializer
from splitcart.permissions import IsAuthenticatedOrAnonymous
from products.utils.get_pricing_stores import get_pricing_stores_map

class SelectedStoreListViewSet(viewsets.ModelViewSet):
    """
    A unified ViewSet for listing, creating, retrieving, updating,
    and deleting SelectedStoreLists.
    """
    serializer_class = SelectedStoreListSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    queryset = SelectedStoreList.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        """
        This queryset is the base for all retrieval operations.
        It ensures that users can only access their own store lists.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None) or self.request.query_params.get('anonymous_id')
            if anonymous_id:
                return self.queryset.filter(anonymous_id=anonymous_id)
            return self.queryset.none()

    def perform_create(self, serializer):
        """
        Logic from SelectedStoreListCreateView.
        Automatically assigns a name on creation.
        """
        if self.request.user.is_authenticated:
            user = self.request.user
            base_name = "List"
            counter = 1
            existing_names = SelectedStoreList.objects.filter(user=user).values_list('name', flat=True)
            new_name = f"{base_name} {counter}"
            while new_name in existing_names:
                counter += 1
                new_name = f"{base_name} {counter}"
            serializer.save(user=user, name=new_name)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None)
            serializer.save(anonymous_id=anonymous_id, name="My Stores")

    def update(self, request, *args, **kwargs):
        """
        Logic from SelectedStoreListRetrieveUpdateDestroyView.
        Injects business logic on update.
        """
        if 'stores' in request.data:
            request.data['is_user_defined'] = True

        if not request.user.is_authenticated and 'name' in request.data:
            raise PermissionDenied("Anonymous users cannot change the store list name.")
        
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request, *args, **kwargs):
        """
        Logic from ActiveStoreListView.
        Gets the most recently used store list and its anchor map.
        """
        store_list = self.get_queryset().order_by('-last_used_at').first()

        if not store_list:
            return Response({
                'store_list': None,
                'anchor_map': None
            }, status=status.HTTP_200_OK)

        store_ids = list(store_list.stores.values_list('id', flat=True))
        anchor_map = get_pricing_stores_map(store_ids)
        
        serializer = self.get_serializer(store_list)

        response_data = {
            'store_list': serializer.data,
            'anchor_map': anchor_map,
        }

        return Response(response_data, status=status.HTTP_200_OK)
