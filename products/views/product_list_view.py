from django.db.models import F, Q, Case, When, Value, IntegerField, Min
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from products.models import Product, ProductPriceSummary
from companies.models import PrimaryCategory
from products.serializers.product_serializer import ProductSerializer
from products.utils.bargain_utils import calculate_bargains
from products.utils.default_companies import get_default_company_ids
from products.utils.product_ordering import get_bargain_first_ordering, _primary_category_slug_filter


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

@method_decorator(cache_page(60 * 60 * 2), name='dispatch')
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def _get_carousel_queryset(self, company_ids, primary_category_slugs):
        """
        Gets a hybrid queryset for carousels using the bargain-first ordering logic.
        """
        CAROUSEL_SIZE = 20
        self.carousel_bargain_map = {} # Reset map for each request

        final_product_ids, bargain_map = get_bargain_first_ordering(
            company_ids, primary_category_slugs, limit=CAROUSEL_SIZE
        )
        self.carousel_bargain_map = bargain_map

        if not final_product_ids:
            return Product.objects.none(), []

        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_product_ids)])
        final_queryset = Product.objects.filter(pk__in=final_product_ids).order_by(preserved_order)

        return final_queryset, company_ids

    def get_queryset(self):
        search_query = self.request.query_params.get('search', None)
        primary_category_slug_param = self.request.query_params.get('primary_category_slug', None)
        primary_category_slugs_param = self.request.query_params.get('primary_category_slugs', None)
        ordering = self.request.query_params.get('ordering', 'default')
        bargain_company_name = self.request.query_params.get('bargain_company', None)

        company_ids = get_default_company_ids()
        if not company_ids:
            return Product.objects.none()

        # --- Bargain Company Filter ---
        if bargain_company_name:
            candidate_product_ids = list(ProductPriceSummary.objects.filter(
                best_possible_discount__gte=5,
                best_possible_discount__lte=70
            ).filter(
                company_count__gte=2
            ).order_by('-best_possible_discount').values_list('product_id', flat=True)[:1000])

            if not candidate_product_ids:
                return Product.objects.none()

            all_bargains = calculate_bargains(candidate_product_ids, company_ids)

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
                'prices__company', 'skus'
            )

        # --- Carousel Logic: Fast-path for performance ---
        if ordering == 'carousel_default' and (primary_category_slug_param or primary_category_slugs_param):
            slugs = []
            if primary_category_slugs_param:
                slugs = [slug.strip() for slug in primary_category_slugs_param.split(',')]
            elif primary_category_slug_param:
                slugs = [primary_category_slug_param]

            queryset, _companies_for_context = self._get_carousel_queryset(company_ids, slugs)
            return queryset.prefetch_related(
                'prices__company', 'skus'
            ).defer('normalized_name_brand_size_variations', 'sizes')

        # --- General Search/Filtering Logic ---
        queryset = Product.objects.filter(prices__company__id__in=company_ids).distinct()

        # Category filtering
        slugs_for_filtering = []
        if primary_category_slugs_param:
            slugs_for_filtering = [slug.strip() for slug in primary_category_slugs_param.split(',')]
        elif primary_category_slug_param:
            try:
                primary_category = PrimaryCategory.objects.prefetch_related('sub_categories').get(slug=primary_category_slug_param)
                slugs_for_filtering = [primary_category.slug] + [sub.slug for sub in primary_category.sub_categories.all()]
            except PrimaryCategory.DoesNotExist:
                return queryset.none()
        
        if slugs_for_filtering:
            queryset = queryset.filter(_primary_category_slug_filter(slugs_for_filtering))


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

        # Final Ordering
        if ordering == 'price_asc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__company__id__in=company_ids))
            ).order_by('min_price')
        elif ordering == 'price_desc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__company__id__in=company_ids))
            ).order_by('-min_price')
        elif ordering == 'unit_price_asc':
             final_queryset = queryset.annotate(
                min_unit_price=Min('prices__unit_price', filter=Q(prices__company__id__in=company_ids))
            ).order_by(F('min_unit_price').asc(nulls_last=True))
        elif ordering == 'default' and slugs_for_filtering and not search_query:
            product_ids, bargain_map = get_bargain_first_ordering(
                company_ids, slugs_for_filtering
            )
            self.bargain_info_map = bargain_map
            
            if not product_ids:
                return Product.objects.none()

            preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)])
            final_queryset = Product.objects.filter(pk__in=product_ids).order_by(preserved_order)
        
        else: # Default search ordering or when no category is specified
            if search_query:
                score = Value(0, output_field=IntegerField())
                for term in search_terms:
                    score += Case(When(name__icontains=term, then=Value(10)), default=Value(0), output_field=IntegerField())
                    score += Case(When(brand__name__icontains=term, then=Value(5)), default=Value(0), output_field=IntegerField())
                queryset = queryset.annotate(search_score=score)
                final_queryset = queryset.order_by('-search_score')
            else:
                # Fallback for non-category, non-search views
                final_queryset = queryset.annotate(
                    min_unit_price=Min('prices__unit_price', filter=Q(prices__company__id__in=company_ids))
                ).order_by(F('min_unit_price').asc(nulls_last=True))

        return final_queryset.prefetch_related(
            'prices__company', 'skus'
        ).defer('normalized_name_brand_size_variations', 'sizes')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add the calculated bargain info for the carousel or bargain search to use
        if hasattr(self, 'bargain_info_map'):
            context['bargain_info_map'] = self.bargain_info_map
        elif hasattr(self, 'carousel_bargain_map'):
            context['bargain_info_map'] = self.carousel_bargain_map
        return context
