from rest_framework import generics
from companies.models import PopularCategory
from ..serializers import PopularCategorySerializer

class PopularCategoryListView(generics.ListAPIView):
    serializer_class = PopularCategorySerializer
    queryset = PopularCategory.objects.all().order_by('name')
    pagination_class = None
