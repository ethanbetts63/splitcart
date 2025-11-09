from rest_framework import generics
from companies.models import PrimaryCategory
from ...serializers import PrimaryCategorySerializer

class PrimaryCategoryListView(generics.ListAPIView):
    serializer_class = PrimaryCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return PrimaryCategory.objects.all()
