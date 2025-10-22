from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from users.models import SelectedStoreList
from api.serializers import SelectedStoreListSerializer

class SelectedStoreListListCreateView(generics.ListCreateAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SelectedStoreList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user

        # Generate a unique name
        base_name = "List"
        counter = 1
        existing_names = SelectedStoreList.objects.filter(user=user).values_list('name', flat=True)

        new_name = f"{base_name} {counter}"
        while new_name in existing_names:
            counter += 1
            new_name = f"{base_name} {counter}"

        serializer.save(user=user, name=new_name)

class SelectedStoreListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [permissions.IsAuthenticated] # Changed to IsAuthenticated
    queryset = SelectedStoreList.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        # Ensure users can only access their own store lists
        return SelectedStoreList.objects.filter(user=self.request.user)