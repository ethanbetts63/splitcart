import json
from splitcart.base_api_view import BaseAPIView
from django.http import JsonResponse
from products.models import Product

class ProductBarcodeView(BaseAPIView):
    """
    An API view to look up barcode information for a given list of Coles SKUs.
    Uses a brute-force Python filtering method because direct JSON lookups are failing.
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

        # Step 1: Broadly query all products that have a SKU associated with Coles.
        all_coles_products = Product.objects.filter(skus__company__name__iexact='Coles').prefetch_related('skus__company')

        # Step 2: Create a map from SKU to barcode information by iterating in Python.
        # This logic is designed to be thorough and "lock in" a good barcode when it's found.
        sku_to_barcode_map = {}
        for p in all_coles_products.iterator(chunk_size=2000):
            # Iterate through the prefetched SKU objects for the product
            for sku_obj in p.skus.all():
                # We can be reasonably sure the company is Coles due to the initial filter,
                # but a check doesn't hurt if products can have SKUs from multiple companies.
                if sku_obj.company.name.lower() != 'coles':
                    continue

                try:
                    sku_int = int(sku_obj.sku)
                    if sku_int in skus_to_lookup:
                        # If we haven't seen this SKU yet, add it.
                        if sku_int not in sku_to_barcode_map:
                            sku_to_barcode_map[sku_int] = {
                                'barcode': p.barcode,
                                'has_no_coles_barcode': p.has_no_coles_barcode
                            }
                        # If we have seen it, only update it if the existing entry has no barcode
                        # and this new product does have one.
                        else:
                            existing_entry = sku_to_barcode_map[sku_int]
                            if not existing_entry.get('barcode') and p.barcode:
                                existing_entry['barcode'] = p.barcode
                                if p.has_no_coles_barcode is not None:
                                    existing_entry['has_no_coles_barcode'] = p.has_no_coles_barcode
                except (ValueError, TypeError):
                    continue
        
        # The API response requires string keys for the JSON object
        response_map_str_keys = {str(k): v for k, v in sku_to_barcode_map.items()}

        return JsonResponse(response_map_str_keys)

