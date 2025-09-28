from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from ..serializers import ProductSerializer

class ProductSubstituteListView(APIView):
    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get up to 5 substitutes for the product
        # The 'substitutes' field is a ManyToMany relationship
        substitutes = product.substitutes.all()[:5] # Limit to 5 as per plan

        # Pass nearby_store_ids from the request query params to the serializer context
        nearby_store_ids = request.query_params.getlist('nearby_store_ids')
        if nearby_store_ids:
            nearby_store_ids = [int(id) for id in nearby_store_ids]

        serializer = ProductSerializer(substitutes, many=True, context={'nearby_store_ids': nearby_store_ids})
        return Response(serializer.data, status=status.HTTP_200_OK)
