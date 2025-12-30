from rest_framework.generics import ListAPIView
from companies.models import Store
from api.serializers import StoreExportSerializer
from api.permissions import IsInternalAPIRequest
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
