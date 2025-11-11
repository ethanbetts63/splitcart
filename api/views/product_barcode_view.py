import json
from .base_api_view import BaseAPIView
from django.http import JsonResponse
from products.models import Product

class ProductBarcodeView(BaseAPIView):
    """
    An API view to look up barcodes for a given list of canonical product names.
    """
    def post(self, request, *args, **kwargs):
        # 1. Validate request body
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or 'names' not in data or not isinstance(data['names'], list):
                return JsonResponse({"error": "Invalid request format. Expected JSON object with a 'names' list."}, status=400)
            names_to_lookup = data['names']
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        # 2. Query the database for products matching the names
        products = Product.objects.filter(
            normalized_name_brand_size__in=names_to_lookup
        ).only('normalized_name_brand_size', 'barcode', 'has_no_coles_barcode')

        # 3. Construct the response dictionary with barcode and flag
        response_map = {
            p.normalized_name_brand_size: {
                'barcode': p.barcode,
                'has_no_coles_barcode': p.has_no_coles_barcode
            }
            for p in products
        }

        return JsonResponse(response_map)
