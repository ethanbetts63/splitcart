from rest_framework import generics
from products.models import Product
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        print("API endpoint /api/products/ was hit.")
        return super().get(request, *args, **kwargs)
