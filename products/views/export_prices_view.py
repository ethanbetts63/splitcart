from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from datetime import date 
from products.models import Price
from data_management.serializers.price_export_serializer import PriceExportSerializer
from splitcart.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportPricesView(ListAPIView):
    """
    A view to export all price data.
    """
    serializer_class = PriceExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
    pagination_class = CursorPagination
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

        scraped_date_gte_str = self.request.query_params.get('scraped_date_gte', None)
        if scraped_date_gte_str:
            try:
                scraped_date_gte = date.fromisoformat(scraped_date_gte_str)
                queryset = queryset.filter(scraped_date__gte=scraped_date_gte)
            except ValueError:
                # Handle invalid date format gracefully, perhaps log a warning
                pass # For now, just ignore invalid date filters

        # For numeric pagination by product ID chunks.
        try:
            product_id_gte = self.request.query_params.get('product_id_gte', None)
            if product_id_gte is not None:
                queryset = queryset.filter(product_id__gte=int(product_id_gte))

            product_id_lt = self.request.query_params.get('product_id_lt', None)
            if product_id_lt is not None:
                queryset = queryset.filter(product_id__lt=int(product_id_lt))
        except (ValueError, TypeError):
            # Ignore if params are not valid integers
            pass

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Directly get values, bypassing the serializer for performance.
        # The fields selected here must match what the client-side script expects.
        values_queryset = queryset.values('product_id', 'store_id', 'price', 'id', 'store__company_id')

        # Manually configure and paginate
        paginator = self.pagination_class()
        paginator.ordering = ['id'] # Explicitly set ordering on the paginator instance

        page = paginator.paginate_queryset(values_queryset, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)

        # This fallback is for cases where pagination is not used.
        return Response(values_queryset)
