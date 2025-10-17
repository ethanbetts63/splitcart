from rest_framework import generics
from companies.models import Category
from ..serializers import PopularCategorySerializer

class PopularCategoryListView(generics.ListAPIView):
    serializer_class = PopularCategorySerializer
    queryset = Category.objects.filter(is_popular=True).order_by('name')
