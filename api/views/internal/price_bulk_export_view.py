from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Price
from api.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class PriceBulkExportView(APIView):
    """
    A dedicated, high-performance view to export prices for a specific
    list of product IDs. Designed for internal use by data generation scripts.
    Accepts a POST request with a JSON body: {"product_ids": [1, 2, 3, ...]}
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    def post(self, request, *args, **kwargs):
        product_ids = request.data.get('product_ids')

        if not isinstance(product_ids, list):
            return Response(
                {"error": "Request body must contain a 'product_ids' list."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not product_ids:
            return Response([], status=status.HTTP_200_OK)

        # Perform a highly efficient query for the given product IDs.
        queryset = Price.objects.filter(product_id__in=product_ids)

        # Directly get values, bypassing the serializer for performance.
        # The fields selected here must match what the BargainGenerator expects.
        values = list(queryset.values('product_id', 'store_id', 'price', 'id', 'store__company_id', 'store__state'))

        return Response(values, status=status.HTTP_200_OK)
