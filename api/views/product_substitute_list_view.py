from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from products.models import Product
from products.models.substitution import ProductSubstitution
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from ..serializers import ProductSubstitutionSerializer

class ProductSubstituteListView(APIView):
    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Base queryset for substitutions
        substitutions_queryset = ProductSubstitution.objects.filter(
            Q(product_a=product) | Q(product_b=product)
        ).order_by('level', '-score')

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
                    
                    # Filter substitutions where the *other* product has prices in nearby stores
                    substitutions_queryset = substitutions_queryset.filter(
                        Q(product_a=product, product_b__price_records__price_entries__store__id__in=nearby_store_ids) |
                        Q(product_b=product, product_a__price_records__price_entries__store__id__in=nearby_store_ids)
                    ).distinct()
                else:
                    # If postcode not found, return empty queryset
                    substitutions_queryset = ProductSubstitution.objects.none()
            except (ValueError, TypeError):
                pass # Invalid radius, ignore filtering

        # Limit to 5 substitutes after filtering
        substitutions = substitutions_queryset[:5]

        # Pass original product_id and nearby_store_ids in context
        context = {
            'original_product_id': product.id,
            'nearby_store_ids': nearby_store_ids
        }
        serializer = ProductSubstitutionSerializer(substitutions, many=True, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)
