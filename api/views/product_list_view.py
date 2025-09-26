from rest_framework import generics, filters
from products.models import Product
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().order_by('name')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
