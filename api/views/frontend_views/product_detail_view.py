from rest_framework.generics import RetrieveAPIView
from products.models import Product
from ...serializers import ProductSerializer

class ProductDetailView(RetrieveAPIView):
    """
    API view to retrieve a single product by its ID.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'
