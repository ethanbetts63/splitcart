from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from products.models import Product
from products.models.substitution import ProductSubstitution
from products.serializers.product_substitution_serializer import ProductSubstitutionSerializer

@method_decorator(cache_page(60 * 60 * 6), name='dispatch')
class ProductSubstituteListView(APIView):
    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        substitutions = ProductSubstitution.objects.filter(
            Q(product_a=product) | Q(product_b=product)
        ).order_by('level', '-score')[:5]

        serializer = ProductSubstitutionSerializer(
            substitutions,
            many=True,
            context={'original_product_id': product.id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
