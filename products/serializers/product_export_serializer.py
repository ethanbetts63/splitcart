from rest_framework import serializers
from products.models import Product


class ProductExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'normalized_name_brand_size',
            'brand_id',
            'size',
            'sizes',
            'primary_category_slugs',
        ]
