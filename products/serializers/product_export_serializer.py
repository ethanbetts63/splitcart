from rest_framework import serializers
from products.models import Product

class ProductExportSerializer(serializers.ModelSerializer):
    # We need the category IDs for the substitution generators
    category = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'normalized_name_brand_size',
            'brand_id',
            'size',
            'sizes',
            'category'
        ]
