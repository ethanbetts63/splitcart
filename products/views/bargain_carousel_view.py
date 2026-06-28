from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from products.models import Product, ProductPriceSummary
from products.serializers.product_serializer import ProductSerializer
from products.utils.bargain_utils import calculate_bargains
from products.utils.default_companies import get_default_company_ids


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class BargainCarouselView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        company_name = self.request.query_params.get('company_name')
        try:
            limit = int(self.request.query_params.get('limit', 20))
        except (ValueError, TypeError):
            limit = 20

        limit = min(limit, 100)

        company_ids = get_default_company_ids()
        if not company_ids:
            return Response([])

        # --- Step 1: Get Potential Bargain Candidates ---
        candidate_limit = 400 if company_name else 200
        candidate_product_ids = list(ProductPriceSummary.objects.filter(
            product__prices__company__id__in=company_ids,
            best_possible_discount__gte=5,
            best_possible_discount__lte=70,
        ).filter(
            company_count__gte=2
        ).distinct().order_by('-best_possible_discount').values_list('product_id', flat=True)[:candidate_limit])

        if not candidate_product_ids:
            return Response([])

        # --- Step 2: Calculate Actual Bargains In-Memory ---
        calculated_bargains = calculate_bargains(candidate_product_ids, company_ids)

        if not calculated_bargains:
            return Response([])

        # --- Filter by Company Name if provided ---
        if company_name:
            calculated_bargains = [
                b for b in calculated_bargains
                if b['cheaper_company_name'].lower() == company_name.lower()
            ]

        # --- Sort, Limit, and Fetch Final Products ---
        sorted_bargains = sorted(calculated_bargains, key=lambda b: b['discount'], reverse=True)
        final_bargain_data = {b['product_id']: b for b in sorted_bargains[:limit]}
        final_product_ids = list(final_bargain_data.keys())

        if not final_product_ids:
            return Response([])

        products = Product.objects.filter(id__in=final_product_ids).prefetch_related(
            'prices__company', 'skus'
        )
        product_map = {p.id: p for p in products}
        sorted_products = [product_map[pid] for pid in final_product_ids if pid in product_map]

        serializer_context = {
            'request': request,
            'bargain_info_map': final_bargain_data,
        }

        serializer = ProductSerializer(sorted_products, many=True, context=serializer_context)
        return Response(serializer.data)
