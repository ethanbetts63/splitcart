from django.db.models import F, Q, Case, When, Value, IntegerField, Min, Subquery, OuterRef
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from products.models import Product, Bargain
from companies.models import StoreGroupMembership
from ...serializers import ProductSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def _get_carousel_queryset(self, anchor_store_ids, primary_category_slugs):
        """
        Gets a hybrid queryset for carousels. It prioritizes the top 20 bargain
        products and fills the remaining slots with the best unit-price products,
        using anchor stores for all price lookups.
        Returns a tuple of (queryset, store_ids_for_context).
        """
        CAROUSEL_SIZE = 20

        # --- Step 1: The incoming store_ids are already anchor_store_ids ---
        if not anchor_store_ids:
            # If no anchors, fall back to prevent showing nothing.
            qs = Product.objects.filter(
                prices__store__id__in=anchor_store_ids,
                category__primary_category__slug__in=primary_category_slugs
            ).annotate(
                min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
            ).order_by('min_unit_price')[:CAROUSEL_SIZE]
            return qs, anchor_store_ids

        # --- Step 2: Get Bargain Products (Fast) ---
        bargain_product_ids = []
        bargain_query = Bargain.objects.filter(
            cheaper_store_id__in=anchor_store_ids,
            expensive_store_id__in=anchor_store_ids,
            product__category__primary_category__slug__in=primary_category_slugs
        ).order_by('-discount_percentage')
        
        potential_bargain_pids = bargain_query.values_list('product_id', flat=True)[:200]
        seen_pids = set()
        for pid in potential_bargain_pids:
            if pid not in seen_pids:
                seen_pids.add(pid)
                bargain_product_ids.append(pid)
            if len(bargain_product_ids) >= CAROUSEL_SIZE:
                break

        # --- Step 3: Get Filler Products (Fast, if needed) ---
        num_bargains = len(bargain_product_ids)
        filler_product_ids = []
        if num_bargains < CAROUSEL_SIZE:
            num_to_fill = CAROUSEL_SIZE - num_bargains
            
            filler_queryset = Product.objects.filter(
                prices__store__id__in=anchor_store_ids, # Use anchors
                category__primary_category__slug__in=primary_category_slugs
            ).exclude(
                pk__in=bargain_product_ids
            ).annotate(
                min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids)) # Use anchors
            ).order_by('min_unit_price')
            
            filler_product_ids = list(filler_queryset.values_list('pk', flat=True)[:num_to_fill])

        # --- Step 4: Combine and Return ---
        final_product_ids = bargain_product_ids + filler_product_ids
        if not final_product_ids:
            return Product.objects.none(), []

        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_product_ids)])
        
        best_bargain_subquery = Bargain.objects.filter(
            product=OuterRef('pk'),
            cheaper_store_id__in=anchor_store_ids,
            expensive_store_id__in=anchor_store_ids
        ).order_by('-discount_percentage')

        final_queryset = Product.objects.filter(pk__in=final_product_ids).annotate(
            best_discount=Subquery(best_bargain_subquery.values('discount_percentage')[:1]),
            cheaper_store_name=Subquery(best_bargain_subquery.values('cheaper_store__store_name')[:1]),
            cheaper_company_name=Subquery(best_bargain_subquery.values('cheaper_store__company__name')[:1])
        ).order_by(preserved_order)
        
        # Return the queryset and the list of stores that should be used for price serialization
        return final_queryset, anchor_store_ids

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')
        search_query = self.request.query_params.get('search', None)
        primary_category_slug_param = self.request.query_params.get('primary_category_slug', None)
        primary_category_slugs_param = self.request.query_params.get('primary_category_slugs', None)
        ordering = self.request.query_params.get('ordering', None)

        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
        except (ValueError, TypeError):
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})

        # --- Carousel Logic: Fast-path for performance ---
        if ordering == 'carousel_default' and (primary_category_slug_param or primary_category_slugs_param):
            slugs = []
            if primary_category_slugs_param:
                slugs = [slug.strip() for slug in primary_category_slugs_param.split(',')]
            elif primary_category_slug_param:
                slugs = [primary_category_slug_param]
            
            # The helper method now returns both the queryset and the store IDs for the context
            # The incoming store_ids are already the anchor_store_ids
            queryset, stores_for_context = self._get_carousel_queryset(store_ids, slugs)
            self.nearby_store_ids = stores_for_context # Set for serializer context
            return queryset.prefetch_related(
                'prices__store__company', 'skus', 'category__primary_category'
            ).defer('normalized_name_brand_size_variations', 'sizes')

        # --- General Search/Filtering Logic ---
        # The incoming store_ids are already the anchor_store_ids
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
        best_bargain_subquery = Bargain.objects.filter(
            product=OuterRef('pk'),
            cheaper_store_id__in=anchor_store_ids,
            expensive_store_id__in=anchor_store_ids
        ).order_by('-discount_percentage')

        queryset = queryset.annotate(
            best_discount=Subquery(best_bargain_subquery.values('discount_percentage')[:1]),
            cheaper_store_name=Subquery(best_bargain_subquery.values('cheaper_store__store_name')[:1]),
            cheaper_company_name=Subquery(best_bargain_subquery.values('cheaper_store__company__name')[:1]),
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
        return context