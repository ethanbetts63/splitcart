from django.db.models import Q, Case, When, Value, IntegerField
from django.views.decorators.cache import cache_page # New import
from django.utils.decorators import method_decorator # New import
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from products.models import Product
from ...serializers import ProductSerializer

@method_decorator(cache_page(3600), name='dispatch') # Apply cache_page decorator
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        print(f"Initial queryset count: {queryset.count()}")

        store_ids_param = self.request.query_params.get('store_ids')
        search_query = self.request.query_params.get('search', None)
        limit_param = self.request.query_params.get('limit')
        primary_category_slug = self.request.query_params.get('primary_category_slug', None) # New line
        print(f"store_ids_param: {store_ids_param}")

        # New: Require store_ids_param
        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            queryset = queryset.filter(
                prices__store__id__in=store_ids
            ).distinct()
            self.nearby_store_ids = store_ids # Store for serializer context
        except (ValueError, TypeError):
            # New: Raise ValidationError for invalid store_ids
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})

        # Filter by primary category slug if provided
        if primary_category_slug:
            queryset = queryset.filter(category__primary_category__slug=primary_category_slug)

        if search_query:
            search_terms = search_query.split()

            # Build the filter query
            filter_q = Q()
            for term in search_terms:
                filter_q |= Q(name__icontains=term)
                filter_q |= Q(brand__name__icontains=term)
                filter_q |= Q(size__icontains=term)
            
            queryset = queryset.filter(filter_q)

            # Build the scoring annotation
            score = Value(0, output_field=IntegerField())
            for term in search_terms:
                score += Case(
                    When(name__icontains=term, then=Value(10)),
                    default=Value(0),
                    output_field=IntegerField()
                )
                score += Case(
                    When(brand__name__icontains=term, then=Value(5)),
                    default=Value(0),
                    output_field=IntegerField()
                )
                score += Case(
                    When(size__icontains=term, then=Value(2)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            
            queryset = queryset.annotate(search_score=score)
            
            # Order by score, then by name
            final_queryset = queryset.order_by('-search_score', 'name')
        else:
            final_queryset = queryset.order_by('name')

        if limit_param:
            try:
                limit = int(limit_param)
                if limit > 50:
                    limit = 50
                final_queryset = final_queryset[:limit]
            except (ValueError, TypeError):
                pass # Ignore invalid limit

        return final_queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context