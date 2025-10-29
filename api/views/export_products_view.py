from rest_framework import serializers, generics
from products.models import Product

# A lean serializer for export
class ProductExportSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'normalized_name', 'category']

class ExportProductsView(generics.ListAPIView):
    """
    API endpoint that allows all products to be exported.
    Provides a lean JSON representation for local processing.
    """
    queryset = Product.objects.all().prefetch_related('category')
    serializer_class = ProductExportSerializer
