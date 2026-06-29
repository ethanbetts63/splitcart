import json
from data_management.views.base_api_view import BaseAPIView
from django.http import JsonResponse
from products.models import SKU

class ProductBarcodeView(BaseAPIView):
    """
    An API view to look up barcode information for a given list of Coles SKUs.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            skus_to_lookup_raw = data.get('skus', [])
            
            # Ensure all SKUs are integers for the lookup set
            skus_to_lookup = set()
            for sku in skus_to_lookup_raw:
                try:
                    skus_to_lookup.add(int(sku))
                except (ValueError, TypeError):
                    continue

        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON or SKU format."}, status=400)

        if not skus_to_lookup:
            return JsonResponse({})

        sku_strings = [str(sku) for sku in skus_to_lookup]
        sku_rows = (
            SKU.objects
            .filter(company__name__iexact='Coles', sku__in=sku_strings)
            .select_related('product')
        )

        sku_to_barcode_map = {
            sku_obj.sku: {
                'barcode': sku_obj.product.barcode,
                'has_no_coles_barcode': sku_obj.product.has_no_coles_barcode,
            }
            for sku_obj in sku_rows
        }
        
        return JsonResponse(sku_to_barcode_map)
