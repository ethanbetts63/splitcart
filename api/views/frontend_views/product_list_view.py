from collections import defaultdict
from django.db.models import F, Q, Case, When, Value, IntegerField, Min, Subquery, OuterRef, Exists
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from products.models import Product, Price, ProductPriceSummary
from data_management.models import SystemSetting
from companies.models import StoreGroupMembership
from ...serializers import ProductSerializer
from ...utils.bargain_utils import calculate_bargains


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

#@method_decorator(cache_page(60 * 60 * 2), name='dispatch')
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def _get_carousel_queryset(self, anchor_store_ids, primary_category_slugs):
        """
        Gets a hybrid queryset for carousels. It prioritizes the top 20 bargain
        products and fills the remaining slots with the best unit-price products.
        """
        CAROUSEL_SIZE = 20
        self.carousel_bargain_map = {} # Reset map for each request

        if not anchor_store_ids:
            return Product.objects.none(), []

        # --- Step 1: Identify potential candidates ---
        candidate_product_ids = list(ProductPriceSummary.objects.filter(
            product__category__primary_category__slug__in=primary_category_slugs,
            product__prices__store__id__in=anchor_store_ids
        ).distinct().order_by('-best_possible_discount').values_list('product_id', flat=True)[:200])

        if not candidate_product_ids:
             # Fallback to simple unit price ordering if no candidates found
            return Product.objects.filter(
                category__primary_category__slug__in=primary_category_slugs,
                prices__store__id__in=anchor_store_ids
            ).distinct().annotate(
                min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
            ).order_by('min_unit_price')[:CAROUSEL_SIZE], anchor_store_ids

        # --- Step 2: Calculate "real" bargains for the candidates ---
        live_prices = Price.objects.filter(
            product_id__in=candidate_product_ids,
            store_id__in=anchor_store_ids
        ).select_related('store__company')

        products_with_prices = defaultdict(list)
        for price in live_prices:
            products_with_prices[price.product_id].append(price)

        calculated_bargains = []
        for product_id, prices in products_with_prices.items():
            if len(prices) < 2:
                continue
            
            company_ids = {p.store.company_id for p in prices}
            is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
            iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}
            if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
                continue

            min_price_obj = min(prices, key=lambda p: p.price)
            max_price_obj = max(prices, key=lambda p: p.price)

            if min_price_obj.price == max_price_obj.price:
                continue

            actual_discount = int(((max_price_obj.price - min_price_obj.price) / max_price_obj.price) * 100)
            if not (5 <= actual_discount <= 70):
                continue
            
            calculated_bargains.append({
                'product_id': product_id, 'discount': actual_discount,
                'cheaper_store_name': min_price_obj.store.store_name,
                'cheaper_company_name': min_price_obj.store.company.name,
            })
        
        sorted_bargains = sorted(calculated_bargains, key=lambda b: b['discount'], reverse=True)
        
        # Store bargain info for serializer context
        self.carousel_bargain_map = {b['product_id']: b for b in sorted_bargains}
        confirmed_bargain_ids = [b['product_id'] for b in sorted_bargains]

        # --- Step 3: Get Filler Products if needed ---
        num_bargains = len(confirmed_bargain_ids)
        filler_product_ids = []
        if num_bargains < CAROUSEL_SIZE:
            num_to_fill = CAROUSEL_SIZE - num_bargains
            
            filler_queryset = Product.objects.filter(
                prices__store__id__in=anchor_store_ids,
                category__primary_category__slug__in=primary_category_slugs
            ).exclude(
                pk__in=confirmed_bargain_ids
            ).annotate(
                min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
            ).order_by('min_unit_price')
            
            filler_product_ids = list(filler_queryset.values_list('pk', flat=True)[:num_to_fill])

        # --- Step 4: Combine and Return ---
        final_product_ids = confirmed_bargain_ids[:CAROUSEL_SIZE] + filler_product_ids
        if not final_product_ids:
            return Product.objects.none(), []

        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_product_ids)])
        final_queryset = Product.objects.filter(pk__in=final_product_ids).order_by(preserved_order)
        
        return final_queryset, anchor_store_ids

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')
        search_query = self.request.query_params.get('search', None)
        primary_category_slug_param = self.request.query_params.get('primary_category_slug', None)
        primary_category_slugs_param = self.request.query_params.get('primary_category_slugs', None)
        ordering = self.request.query_params.get('ordering', None)
        bargain_company_name = self.request.query_params.get('bargain_company', None)

        store_ids = []
        if store_ids_param:
            try:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            except (ValueError, TypeError):
                raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})
        else:
            default_stores = cache.get('default_anchor_stores')
            if default_stores is None:
                try:
                    setting = SystemSetting.objects.get(key='default_anchor_stores')
                    default_stores = setting.value
                    cache.set('default_anchor_stores', default_stores, 60 * 60)
                except SystemSetting.DoesNotExist:
                    default_stores = []
            store_ids = default_stores

        if not store_ids:
            return Product.objects.none()
        
        self.nearby_store_ids = store_ids

        # --- Bargain Company Filter ---
        if bargain_company_name:
            candidate_product_ids = list(ProductPriceSummary.objects.filter(
                best_possible_discount__gte=5,
                best_possible_discount__lte=70
            ).filter(
                Q(company_count__gte=2) | Q(iga_store_count__gte=2)
            ).order_by('-best_possible_discount').values_list('product_id', flat=True)[:1000])

            if not candidate_product_ids:
                return Product.objects.none()

            all_bargains = calculate_bargains(candidate_product_ids, store_ids)

            company_bargains = [
                b for b in all_bargains
                if b['cheaper_company_name'].lower() == bargain_company_name.lower()
            ]

            sorted_bargains = sorted(company_bargains, key=lambda b: b['discount'], reverse=True)
            
            self.bargain_info_map = {b['product_id']: b for b in sorted_bargains}
            final_product_ids = list(self.bargain_info_map.keys())

            if not final_product_ids:
                return Product.objects.none()

            preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_product_ids)])
            return Product.objects.filter(pk__in=final_product_ids).order_by(preserved_order).prefetch_related(
                'prices__store__company', 'skus', 'category__primary_category'
            )

        # --- Carousel Logic: Fast-path for performance ---
        if ordering == 'carousel_default' and (primary_category_slug_param or primary_category_slugs_param):
            slugs = []
            if primary_category_slugs_param:
                slugs = [slug.strip() for slug in primary_category_slugs_param.split(',')]
            elif primary_category_slug_param:
                slugs = [primary_category_slug_param]
            
            queryset, stores_for_context = self._get_carousel_queryset(store_ids, slugs)
            self.nearby_store_ids = stores_for_context 
            return queryset.prefetch_related(
                'prices__store__company', 'skus', 'category__primary_category'
            ).defer('normalized_name_brand_size_variations', 'sizes')

        # --- General Search/Filtering Logic ---
        anchor_store_ids = store_ids
        self.nearby_store_ids = anchor_store_ids
        queryset = Product.objects.filter(prices__store__id__in=anchor_store_ids).distinct()

        # Category filtering
        if primary_category_slugs_param:
            slugs = [slug.strip() for slug in primary_category_slugs_param.split(',')]
            queryset = queryset.filter(category__primary_category__slug__in=slugs)
        elif primary_category_slug_param:
            queryset = queryset.filter(category__primary_category__slug=primary_category_slug_param)

        # Search term filtering
        search_terms = []
        if search_query:
            search_terms = search_query.split()
            filter_q = Q()
            for term in search_terms:
                filter_q |= Q(name__icontains=term)
                filter_q |= Q(brand__name__icontains=term)
                filter_q |= Q(size__icontains=term)
            queryset = queryset.filter(filter_q)

        # Annotations for sorting
        summary_subquery = ProductPriceSummary.objects.filter(product=OuterRef('pk'))

        queryset = queryset.annotate(
            best_discount=Subquery(summary_subquery.values('best_possible_discount')[:1]),
            min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
        )

        # Final Ordering
        if ordering == 'price_asc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=anchor_store_ids))
            ).order_by('min_price')
        elif ordering == 'price_desc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=anchor_store_ids))
            ).order_by('-min_price')
        elif ordering == 'unit_price_asc':
            final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))
        else: # Default search ordering
            if search_query:
                score = Value(0, output_field=IntegerField())
                for term in search_terms:
                    score += Case(When(name__icontains=term, then=Value(10)), default=Value(0), output_field=IntegerField())
                    score += Case(When(brand__name__icontains=term, then=Value(5)), default=Value(0), output_field=IntegerField())
                queryset = queryset.annotate(search_score=score)
                final_queryset = queryset.order_by('-search_score', F('best_discount').desc(nulls_last=True))
            else:
                final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))

        return final_queryset.prefetch_related(
            'prices__store__company', 'skus', 'category__primary_category'
        ).defer('normalized_name_brand_size_variations', 'sizes')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        # Add the calculated bargain info for the carousel or bargain search to use
        if hasattr(self, 'bargain_info_map'):
            context['bargain_info_map'] = self.bargain_info_map
        elif hasattr(self, 'carousel_bargain_map'):
            context['bargain_info_map'] = self.carousel_bargain_map
        return context