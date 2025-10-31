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