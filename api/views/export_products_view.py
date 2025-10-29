from rest_framework import serializers, generics
from products.models import Product

# A lean serializer for exporting products for local processing
class ProductExportSerializer(serializers.ModelSerializer):
    # We need the category IDs for the substitution generators
    category = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'normalized_name',
            'brand_id',
            'size',
            'unit_of_measure',
            'category'
        ]

class ExportProductsView(generics.ListAPIView):
    """
    API endpoint that allows all products to be exported.
    Provides a lean JSON representation for local processing.
    """
    pagination_class = None  # Disable pagination
    queryset = Product.objects.all().prefetch_related('category')
    serializer_class = ProductExportSerializer