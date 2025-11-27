from decimal import Decimal
from django.db.models import F, Q, Case, When, Value, IntegerField, Min, Subquery, OuterRef
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from products.models import Product, Price, Bargain
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

    @method_decorator(cache_page(60 * 60 * 6)) # Cache for 6 hours
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.all()

        store_ids_param = self.request.query_params.get('store_ids')
        search_query = self.request.query_params.get('search', None)
        primary_category_slug = self.request.query_params.get('primary_category_slug', None)
        primary_category_slugs = self.request.query_params.get('primary_category_slugs', None)
        ordering = self.request.query_params.get('ordering', None)

        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            queryset = queryset.filter(
                prices__store__id__in=store_ids
            ).distinct()
            self.nearby_store_ids = store_ids
        except (ValueError, TypeError):
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})



        if primary_category_slugs:
            slugs = [slug.strip() for slug in primary_category_slugs.split(',')]
            queryset = queryset.filter(category__primary_category__slug__in=slugs)
        elif primary_category_slug:
            queryset = queryset.filter(category__primary_category__slug=primary_category_slug)

        search_terms = []
        if search_query:
            search_terms = search_query.split()
            filter_q = Q()
            for term in search_terms:
                filter_q |= Q(name__icontains=term)
                filter_q |= Q(brand__name__icontains=term)
                filter_q |= Q(size__icontains=term)
            queryset = queryset.filter(filter_q)

        queryset = queryset.annotate(
            min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=store_ids))
        )

        if ordering == 'carousel_default':
            final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))
        elif ordering == 'price_asc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=store_ids))
            ).order_by('min_price')
        elif ordering == 'price_desc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=store_ids))
            ).order_by('-min_price')
        elif ordering == 'unit_price_asc':
            final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))
        else:
            # Default ordering logic
            if search_query:
                score = Value(0, output_field=IntegerField())
                for term in search_terms:
                    score += Case(When(name__icontains=term, then=Value(10)), default=Value(0), output_field=IntegerField())
                    score += Case(When(brand__name__icontains=term, then=Value(5)), default=Value(0), output_field=IntegerField())
                    score += Case(When(size__icontains=term, then=Value(2)), default=Value(0), output_field=IntegerField())
                
                queryset = queryset.annotate(search_score=score)
                final_queryset = queryset.order_by('-search_score', F('min_unit_price').asc(nulls_last=True))
            else:
                final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))

        return final_queryset.prefetch_related('prices__store__company', 'skus')

    # The complex 'list' method is no longer needed, as the default implementation
    # from ListAPIView will now work correctly with the annotated queryset.

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context