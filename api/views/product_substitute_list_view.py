from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from ..serializers import ProductSerializer

class ProductSubstituteListView(APIView):
    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        substitutes_queryset = product.substitutes.all() # Get all substitutes first

        postcode_param = request.query_params.get('postcode')
        radius_param = request.query_params.get('radius')
        
        nearby_store_ids = None
        if postcode_param and radius_param:
            try:
                radius = float(radius_param)
                ref_postcode = Postcode.objects.filter(postcode=postcode_param).first()

                if ref_postcode:
                    nearby_stores = get_nearby_stores(ref_postcode, radius)
                    nearby_store_ids = [store.id for store in nearby_stores]
                    
                    # Filter substitutes to only include those with prices in nearby stores
                    substitutes_queryset = substitutes_queryset.filter(
                        price_records__price_entries__store__id__in=nearby_store_ids
                    ).distinct()
                else:
                    # If postcode not found, return empty queryset
                    substitutes_queryset = Product.objects.none()
            except (ValueError, TypeError):
                pass # Invalid radius, ignore filtering

        # Limit to 5 substitutes after filtering
        substitutes = substitutes_queryset[:5]

        serializer = ProductSerializer(substitutes, many=True, context={'nearby_store_ids': nearby_store_ids})
        return Response(serializer.data, status=status.HTTP_200_OK)
