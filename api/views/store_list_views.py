from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from users.models import SelectedStoreList
from api.serializers import SelectedStoreListSerializer

class SelectedStoreListListCreateView(generics.ListCreateAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Adjust permissions as needed

    def get_queryset(self):
        # Filter by authenticated user or anonymous_id
        if self.request.user.is_authenticated:
            return SelectedStoreList.objects.filter(user=self.request.user)
        # For anonymous users, we'll need to get anonymous_id from cookie/header
        # This part will be implemented later with anonymous user handling middleware
        return SelectedStoreList.objects.none() # For now, anonymous users see no lists

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            # For anonymous users, save with anonymous_id
            # This part will be implemented later with anonymous user handling middleware
            pass # For now, anonymous users cannot create lists

class SelectedStoreListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = SelectedStoreList.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        # Ensure users can only access their own store lists
        if self.request.user.is_authenticated:
            return SelectedStoreList.objects.filter(user=self.request.user)
        # For anonymous users, we'll need to get anonymous_id from cookie/header
        # This part will be implemented later with anonymous user handling middleware
        return SelectedStoreList.objects.none()
