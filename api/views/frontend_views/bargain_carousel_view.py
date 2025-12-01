from collections import defaultdict
from django.db import models
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from products.models import Product, Price, ProductPriceSummary
from companies.models import Company
from ...serializers import ProductSerializer


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

        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            user_store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
        except (ValueError, TypeError):
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})

        if not user_store_ids:
            return Response([])

        # --- Step 1: Get Potential Bargain Candidates ---
        # Widen the net when filtering by a specific company
        candidate_limit = 400 if company_name else 200
        candidate_product_ids = list(ProductPriceSummary.objects.filter(
            best_possible_discount__gte=5,
            best_possible_discount__lte=70,
        ).filter(
            models.Q(company_count__gte=2) | models.Q(iga_store_count__gte=2)
        ).order_by('-best_possible_discount').values_list('product_id', flat=True)[:candidate_limit])

        if not candidate_product_ids:
            return Response([])

        # --- Step 2: Fetch Relevant Live Prices ---
        live_prices = Price.objects.filter(
            product_id__in=candidate_product_ids,
            store_id__in=user_store_ids
        ).select_related('store__company')

        # --- Step 3: Calculate Actual Bargains In-Memory ---
        products_with_prices = defaultdict(list)
        for price in live_prices:
            products_with_prices[price.product_id].append(price)

        calculated_bargains = []
        for product_id, prices in products_with_prices.items():
            if len(prices) < 2:
                continue
            
            # Check for cross-company/IGA price difference
            company_ids = {p.store.company_id for p in prices}
            is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
            iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}
            
            if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
                continue

            min_price_obj = min(prices, key=lambda p: p.price)
            max_price_obj = max(prices, key=lambda p: p.price)

            if min_price_obj.price == max_price_obj.price:
                continue

            # Calculate actual discount and check if it's in the valid range
            actual_discount = int(((max_price_obj.price - min_price_obj.price) / max_price_obj.price) * 100)
            
            if not (5 <= actual_discount <= 70):
                continue
            
            calculated_bargains.append({
                'product_id': product_id,
                'discount': actual_discount,
                'cheaper_store_name': min_price_obj.store.store_name,
                'cheaper_company_name': min_price_obj.store.company.name,
            })

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
