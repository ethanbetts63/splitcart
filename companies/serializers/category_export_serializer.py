from rest_framework import serializers
from companies.models import Category

class CategoryExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        # The 'company' foreign key will be serialized to its ID by default.
        fields = ['id', 'name', 'company']
