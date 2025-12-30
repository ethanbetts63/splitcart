from rest_framework.generics import ListAPIView
from companies.models import Store
from companies.serializers.store_export_serializer import StoreExportSerializer
from splitcart.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportStoresView(ListAPIView):
    """
    A view to export all store data.
    """
    queryset = Store.objects.all().select_related('company', 'division')
    serializer_class = StoreExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
