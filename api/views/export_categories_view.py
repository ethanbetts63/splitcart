from rest_framework import serializers, generics
from companies.models import Category
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest

# A lean serializer for exporting categories
class CategoryExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        # The 'company' foreign key will be serialized to its ID by default.
        fields = ['id', 'name', 'company']

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

class CategoryWithProductsExportSerializer(serializers.ModelSerializer):
    product_ids = serializers.PrimaryKeyRelatedField(
        source='products',
        many=True,
        read_only=True
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'company', 'product_ids']

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