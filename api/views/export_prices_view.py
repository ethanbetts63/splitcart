from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination # New import
from products.models import Price
from api.serializers import PriceExportSerializer
from api.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportPricesView(ListAPIView):
    """
    A view to export all price data.
    """
    serializer_class = PriceExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    pagination_class = CursorPagination # New: Use CursorPagination

    def get_queryset(self):
        """
        Optionally restricts the returned prices to a given set of stores,
        by filtering against a `store_ids` query parameter in the URL.
        """
        queryset = Price.objects.order_by('id') # Explicitly order by ID for pagination
        store_ids_str = self.request.query_params.get('store_ids', None)
        if store_ids_str:
            store_ids = [int(sid) for sid in store_ids_str.split(',')]
            queryset = queryset.filter(store_id__in=store_ids)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Directly get values, bypassing the serializer for performance.
        # The fields selected here must match what the client-side script expects.
        values_queryset = queryset.values('product_id', 'store_id', 'price', 'id')

        # Manually configure and paginate
        paginator = self.pagination_class()
        paginator.ordering = ['id'] # Explicitly set ordering on the paginator instance

        page = paginator.paginate_queryset(values_queryset, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)

        # This fallback is for cases where pagination is not used.
        return Response(values_queryset)
