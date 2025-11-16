from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from users.models import SelectedStoreList
from api.permissions import IsAuthenticatedOrAnonymous
from api.serializers import SelectedStoreListSerializer

class SelectedStoreListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    queryset = SelectedStoreList.objects.all()
    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        if not request.user.is_authenticated and 'name' in request.data:
            raise PermissionDenied("Anonymous users cannot change the store list name.")
        
        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()        
        return response

    def get_queryset(self):
        # Ensure users can only access their own store lists
        if self.request.user.is_authenticated:
            return SelectedStoreList.objects.filter(user=self.request.user)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None)
            if anonymous_id:
                return SelectedStoreList.objects.filter(anonymous_id=anonymous_id)
            return SelectedStoreList.objects.none()
