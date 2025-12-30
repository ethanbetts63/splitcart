from rest_framework import generics
from companies.models import CategoryLink
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest
from ..serializers.category_link_export_serializer import CategoryLinkExportSerializer

class ExportCategoryLinksView(generics.ListAPIView):
    """
    API endpoint that allows all category links to be exported.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    queryset = CategoryLink.objects.all()
    serializer_class = CategoryLinkExportSerializer
