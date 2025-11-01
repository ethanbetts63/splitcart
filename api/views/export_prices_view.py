from rest_framework.generics import ListAPIView
from products.models import Price
from api.serializers import PriceExportSerializer
from api.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportPricesView(ListAPIView):
    """
    A view to export all price data.
    """
    queryset = Price.objects.all().select_related('price_record')
    serializer_class = PriceExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
