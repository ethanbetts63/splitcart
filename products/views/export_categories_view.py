from rest_framework import generics
from companies.models import Category
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest
from companies.serializers.category_export_serializer import CategoryExportSerializer
from companies.serializers.category_with_products_export_serializer import CategoryWithProductsExportSerializer

class ExportCategoriesView(generics.ListAPIView):
    """
    API endpoint that allows all categories to be exported.
    Provides a lean JSON representation for local processing.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    queryset = Category.objects.all()
    serializer_class = CategoryExportSerializer

class ExportCategoriesWithProductsView(generics.ListAPIView):
    """
    API endpoint that allows all categories to be exported, including a list
    of IDs for the products within each category.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    queryset = Category.objects.all().prefetch_related('products')
    serializer_class = CategoryWithProductsExportSerializer