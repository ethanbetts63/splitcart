from rest_framework import generics
from products.models import Product
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest
from ..serializers.product_export_serializer import ProductExportSerializer

class ExportProductsView(generics.ListAPIView):
    """
    API endpoint that allows all products to be exported.
    Provides a lean JSON representation for local processing.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    queryset = Product.objects.all().prefetch_related('category')
    serializer_class = ProductExportSerializer