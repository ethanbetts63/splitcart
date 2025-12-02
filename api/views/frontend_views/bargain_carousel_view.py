from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response 
from rest_framework.views import APIView      
from rest_framework.permissions import AllowAny
from products.models import Product, ProductPriceSummary
from data_management.models import SystemSetting
from ...serializers import ProductSerializer
from ...utils.bargain_utils import calculate_bargains


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class BargainCarouselView(APIView):
    """
    An optimized view to serve products for the "Bargains" carousel using a hybrid calculation model.
    
    This view uses a three-step process for performance and accuracy:
    1.  It quickly finds a list of candidate products using the ProductPriceSummary model.
    2.  It fetches live prices for those candidates based on the user's selected stores.
    3.  It calculates the true, user-specific bargain in memory and returns the sorted results.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        store_ids_param = self.request.query_params.get('store_ids')
        company_name = self.request.query_params.get('company_name') # New parameter
        try:
            limit = int(self.request.query_params.get('limit', 20))
        except (ValueError, TypeError):
            limit = 20
        
        limit = min(limit, 100)

        user_store_ids = []
        if store_ids_param:
            try:
                user_store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            except (ValueError, TypeError):
                raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})
        else:
            # If no store IDs are provided, fetch the default list from SystemSetting
            default_stores = cache.get('default_anchor_stores')
            if default_stores is None:
                try:
                    setting = SystemSetting.objects.get(key='default_anchor_stores')
                    default_stores = setting.value
                    cache.set('default_anchor_stores', default_stores, 60 * 60) # Cache for 1 hour
                except SystemSetting.DoesNotExist:
                    default_stores = []
            user_store_ids = default_stores

        if not user_store_ids:
            # This can happen if param is empty or setting doesn't exist
            return Response([])

        # --- Step 1: Get Potential Bargain Candidates ---
        # Widen the net when filtering by a specific company
        candidate_limit = 400 if company_name else 200
        candidate_product_ids = list(ProductPriceSummary.objects.filter(
            product__prices__store__id__in=user_store_ids,
            best_possible_discount__gte=5,
            best_possible_discount__lte=70,
        ).filter(
            models.Q(company_count__gte=2) | models.Q(iga_store_count__gte=2)
        ).distinct().order_by('-best_possible_discount').values_list('product_id', flat=True)[:candidate_limit])

        if not candidate_product_ids:
            return Response([])

        # --- Step 2: Calculate Actual Bargains In-Memory using the utility ---
        calculated_bargains = calculate_bargains(candidate_product_ids, user_store_ids)

        if not calculated_bargains:
            return Response([])

        # --- New Step: Filter by Company Name if provided ---
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

        # Fetch the product objects and preserve the sorted order
        products = Product.objects.filter(id__in=final_product_ids).prefetch_related(
            'prices__store__company', 'skus', 'category__primary_category'
        )
        product_map = {p.id: p for p in products}
        
        # Build the final list in the correct order
        sorted_products = [product_map[pid] for pid in final_product_ids if pid in product_map]
        
        # --- Serialize with Context ---
        serializer_context = {
            'request': request,
            'nearby_store_ids': user_store_ids,
            'bargain_info_map': final_bargain_data, # Pass our calculated data to the serializer
        }
        
        serializer = ProductSerializer(sorted_products, many=True, context=serializer_context)
        
        return Response(serializer.data)
