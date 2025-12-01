from rest_framework import serializers
from companies.models import Category

class CategoryWithProductsExportSerializer(serializers.ModelSerializer):
    company = serializers.StringRelatedField(source='company')
    product_ids = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'company', 'parents', 'product_ids')

    def get_product_ids(self, obj):
        return list(obj.products.values_list('id', flat=True))
