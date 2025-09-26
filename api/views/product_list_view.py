from rest_framework import generics
from products.models import Product
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
