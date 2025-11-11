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
        print("--- ProductBarcodeView: Received request ---")
        # 1. Validate request body
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or 'skus' not in data or not isinstance(data['skus'], list):
                return JsonResponse({"error": "Invalid request format. Expected JSON object with a 'skus' list."}, status=400)
            skus_to_lookup = data['skus']
            print(f"--- ProductBarcodeView: Looking up {len(skus_to_lookup)} SKUs ---")
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON or SKU format."}, status=400)

        # 2. Query the database for products matching the SKUs
        # NOTE: Using Q objects with `contains` is less performant than `overlap` for large lists,
        # but is used here to ensure correctness. This can be optimized later if performance becomes an issue.
        query = Q()
        for sku in skus_to_lookup:
            query |= Q(company_skus__coles__contains=sku)
        
        products = Product.objects.filter(query).only('company_skus', 'barcode', 'has_no_coles_barcode')
        print(f"--- ProductBarcodeView: Found {len(products)} matching products in DB ---")

        # 3. Construct the response dictionary, mapping SKU to product data
        response_map = {}
        # Create a set of stringified SKUs for faster lookups
        skus_to_lookup_set = set(map(str, skus_to_lookup))

        for p in products:
            # Using .get is safer
            product_coles_skus = p.company_skus.get('coles', [])
            for product_sku in product_coles_skus:
                str_product_sku = str(product_sku)
                if str_product_sku in skus_to_lookup_set:
                    response_map[str_product_sku] = {
                        'barcode': p.barcode,
                        'has_no_coles_barcode': p.has_no_coles_barcode
                    }
        
        print(f"--- ProductBarcodeView: Returning map for {len(response_map)} SKUs ---")
        return JsonResponse(response_map)

