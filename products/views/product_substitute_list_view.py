from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from products.models import Product, Price
from products.models.substitution import ProductSubstitution
from products.serializers.product_substitution_serializer import ProductSubstitutionSerializer

@method_decorator(cache_page(60 * 60 * 6), name='dispatch')
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

        store_ids_param = request.query_params.get('store_ids')
        nearby_store_ids = None
        if store_ids_param:
            try:
                nearby_store_ids = [int(sid) for sid in store_ids_param.split(',')]
                store_prices = Price.objects.for_stores(nearby_store_ids)
                substitutions_queryset = substitutions_queryset.filter(
                    Q(product_a=product, product_b__prices__in=store_prices) |
                    Q(product_b=product, product_a__prices__in=store_prices)
                ).distinct()
            except (ValueError, TypeError):
                pass

        substitutions = substitutions_queryset[:5]

        context = {
            'original_product_id': product.id,
            'nearby_store_ids': nearby_store_ids
        }
        serializer = ProductSubstitutionSerializer(substitutions, many=True, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)
