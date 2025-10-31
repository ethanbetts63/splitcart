from rest_framework import serializers, generics
from companies.models import CategoryLink
from api.permissions import IsInternalAPIRequest

class CategoryLinkExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryLink
        fields = ['category_a_id', 'category_b_id', 'link_type']

class ExportCategoryLinksView(generics.ListAPIView):
    """
    API endpoint that allows all category links to be exported.
    """
    permission_classes = [IsInternalAPIRequest]
    queryset = CategoryLink.objects.all()
    serializer_class = CategoryLinkExportSerializer
