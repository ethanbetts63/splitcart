from rest_framework import serializers, generics
from companies.models import Category

# A lean serializer for exporting categories
class CategoryExportSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'company']

class ExportCategoriesView(generics.ListAPIView):
    """
    API endpoint that allows all categories to be exported.
    Provides a lean JSON representation for local processing.
    """
    queryset = Category.objects.all().select_related('company')
    serializer_class = CategoryExportSerializer
