from rest_framework.generics import RetrieveAPIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from products.models import Product
from products.serializers.product_serializer import ProductSerializer

@method_decorator(cache_page(60 * 30), name='dispatch')
class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.prefetch_related('prices__company', 'skus')
    serializer_class = ProductSerializer
    lookup_field = 'pk'
