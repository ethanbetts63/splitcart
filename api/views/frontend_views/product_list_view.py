from decimal import Decimal
from django.db.models import F, Q, Case, When, Value, IntegerField, Min
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from products.models import Product, Price
from ...serializers import ProductSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

@method_decorator(cache_page(21600), name='dispatch')
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

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

        # Annotate with min_unit_price for sorting and serialization.
        queryset = queryset.annotate(
            min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=store_ids))
        )

        if ordering == 'price_asc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=store_ids))
            ).order_by('min_price')
        elif ordering == 'price_desc':
            final_queryset = queryset.annotate(
                min_price=Min('prices__price', filter=Q(prices__store__id__in=store_ids))
            ).order_by('-min_price')
        elif ordering == 'unit_price_asc':
            final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))
        elif ordering == 'carousel_default':
            # This special ordering is now handled entirely within the list() method.
            final_queryset = queryset
        else:
            # Default ordering logic for search and category pages
            if search_query:
                score = Value(0, output_field=IntegerField())
                for term in search_terms:
                    score += Case(When(name__icontains=term, then=Value(10)), default=Value(0), output_field=IntegerField())
                    score += Case(When(brand__name__icontains=term, then=Value(5)), default=Value(0), output_field=IntegerField())
                    score += Case(When(size__icontains=term, then=Value(2)), default=Value(0), output_field=IntegerField())
                
                queryset = queryset.annotate(search_score=score)
                final_queryset = queryset.order_by('-search_score')
            else:
                # For category pages without a specific sort, default to unit price
                final_queryset = queryset.order_by(F('min_unit_price').asc(nulls_last=True))

        return final_queryset

    def list(self, request, *args, **kwargs):
        ordering = self.request.query_params.get('ordering', None)
        
        # If not the special carousel ordering, use the default ListAPIView behavior
        if ordering != 'carousel_default':
            return super().list(request, *args, **kwargs)

        # Custom logic for 'carousel_default' ordering
        queryset = self.filter_queryset(self.get_queryset())

        # 1. Isolate the Bargains
        bargain_qs = queryset.filter(has_bargain=True)
        non_bargain_qs = queryset.filter(has_bargain=False).order_by(F('min_unit_price').asc(nulls_last=True))

        # 2. Calculate Discounts On-the-Fly for bargain products
        store_ids = getattr(self, 'nearby_store_ids', [])
        prices_for_bargains = Price.objects.filter(
            product__in=bargain_qs,
            store_id__in=store_ids
        ).select_related('store__company')

        prices_by_product_id = {}
        for price in prices_for_bargains:
            if price.product_id not in prices_by_product_id:
                prices_by_product_id[price.product_id] = []
            prices_by_product_id[price.product_id].append(price)

        bargain_products_with_discount = []
        for product in bargain_qs:
            product_prices = prices_by_product_id.get(product.id, [])
            
            company_prices = {}
            for p in product_prices:
                company_name = p.store.company.name
                if company_name not in company_prices:
                    company_prices[company_name] = []
                company_prices[company_name].append(p.price)

            discount = 0
            if len(company_prices) >= 2:
                # Get the lowest price from each company, then compare those lowest prices
                min_prices_per_company = [min(prices) for prices in company_prices.values()]
                
                min_price = min(min_prices_per_company)
                max_price = max(min_prices_per_company)

                if min_price > 0 and max_price > min_price:
                    calculated_discount = round(((max_price - min_price) / max_price) * 100)
                    # This is the range for user-facing bargains in the serializer
                    if 10 <= calculated_discount <= 75:
                        discount = calculated_discount
            
            bargain_products_with_discount.append({'product': product, 'discount': discount})

        # 3. Sort the Bargains
        bargain_products_with_discount.sort(key=lambda x: x['discount'], reverse=True)
        sorted_bargain_products = [item['product'] for item in bargain_products_with_discount]

        # 4. Combine and Paginate
        final_product_list = sorted_bargain_products + list(non_bargain_qs)

        page = self.paginate_queryset(final_product_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(final_product_list, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context