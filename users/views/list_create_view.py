from rest_framework import generics
from api.permissions import IsAuthenticatedOrAnonymous
from users.models import SelectedStoreList
from api.serializers import SelectedStoreListSerializer

class SelectedStoreListCreateView(generics.ListCreateAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return SelectedStoreList.objects.filter(user=self.request.user)
        else:
            anonymous_id = self.request.query_params.get('anonymous_id')
            if anonymous_id:
                return SelectedStoreList.objects.filter(anonymous_id=anonymous_id)
            return SelectedStoreList.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            user = self.request.user

            # Generate a unique name for the authenticated user
            base_name = "List"
            counter = 1
            existing_names = SelectedStoreList.objects.filter(user=user).values_list('name', flat=True)
            new_name = f"{base_name} {counter}"
            while new_name in existing_names:
                counter += 1
                new_name = f"{base_name} {counter}"

            serializer.save(user=user, name=new_name)
        else:
            # Handle anonymous user
            anonymous_id = getattr(self.request, 'anonymous_id', None)
            # For anonymous users, we can use a generic name since they won't see a list of lists.
            serializer.save(anonymous_id=anonymous_id, name="My Stores")
