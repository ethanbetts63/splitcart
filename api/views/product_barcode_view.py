import json
from .base_api_view import BaseAPIView
from django.http import JsonResponse
from django.db.models import Q
from products.models import Product

class ProductBarcodeView(BaseAPIView):
    """
    An API view to look up barcode information for a given list of Coles SKUs.
    """
    def post(self, request, *args, **kwargs):
        # 1. Validate request body
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or 'skus' not in data or not isinstance(data['skus'], list):
                return JsonResponse({"error": "Invalid request format. Expected JSON object with a 'skus' list."}, status=400)
            skus_to_lookup = data['skus']
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON or SKU format."}, status=400)

        # 2. Query the database for products matching the SKUs
        # Use the efficient __overlap lookup to check for any common elements between the db array and the lookup list.
        products = Product.objects.filter(
            company_skus__coles__overlap=skus_to_lookup
        ).only('company_skus', 'barcode', 'has_no_coles_barcode')

        # 3. Construct the response dictionary, mapping SKU to product data
        response_map = {}
        for p in products:
            product_coles_skus = p.company_skus.get('coles', [])
            for requested_sku in skus_to_lookup:
                # Ensure we compare numbers to numbers, but use strings for the JSON response keys.
                if requested_sku in product_coles_skus:
                    response_map[str(requested_sku)] = {
                        'barcode': p.barcode,
                        'has_no_coles_barcode': p.has_no_coles_barcode
                    }
        
        return JsonResponse(response_map)

