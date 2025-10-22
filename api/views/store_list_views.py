from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from users.models import SelectedStoreList
from api.serializers import SelectedStoreListSerializer

class SelectedStoreListListCreateView(generics.ListCreateAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticated] # Changed to IsAuthenticated

    def get_queryset(self):
        # Only return store lists for the authenticated user
        return SelectedStoreList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically associate the store list with the authenticated user
        serializer.save(user=self.request.user)

class SelectedStoreListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticated] # Changed to IsAuthenticated
    queryset = SelectedStoreList.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        # Ensure users can only access their own store lists
        return SelectedStoreList.objects.filter(user=self.request.user)