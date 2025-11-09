from rest_framework.generics import ListAPIView
from products.models import Price
from api.serializers import PriceExportSerializer
from api.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportPricesView(ListAPIView):
    """
    A view to export all price data.
    """
    def get_queryset(self):
        """
        Optionally restricts the returned prices to a given set of stores,
        by filtering against a `store_ids` query parameter in the URL.
        """
        queryset = Price.objects.all()
        store_ids_str = self.request.query_params.get('store_ids', None)
        if store_ids_str:
            store_ids = [int(sid) for sid in store_ids_str.split(',')]
            queryset = queryset.filter(store_id__in=store_ids)
        return queryset

    serializer_class = PriceExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
