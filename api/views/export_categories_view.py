from rest_framework import serializers, generics
from companies.models import Category

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
    pagination_class = None # Disable pagination for this view
    queryset = Category.objects.all()
    serializer_class = CategoryExportSerializer