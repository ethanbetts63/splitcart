from rest_framework import serializers
from companies.models import Category

class CategoryWithProductsExportSerializer(serializers.ModelSerializer):
    product_ids = serializers.PrimaryKeyRelatedField(
        source='products',
        many=True,
        read_only=True
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'company', 'product_ids']
