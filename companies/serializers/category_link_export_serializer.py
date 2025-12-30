from rest_framework import serializers
from companies.models import CategoryLink

class CategoryLinkExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryLink
        fields = ['category_a_id', 'category_b_id', 'link_type']
