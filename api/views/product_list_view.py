from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework import generics
from products.models import Product
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        store_ids_param = self.request.query_params.get('store_ids')
        search_query = self.request.query_params.get('search', None)

        if store_ids_param:
            try:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
                queryset = queryset.filter(
                    price_records__price_entries__store__id__in=store_ids
                ).distinct()
                self.nearby_store_ids = store_ids # Store for serializer context
            except (ValueError, TypeError):
                pass # Invalid store_ids, ignore filtering

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
            return queryset.order_by('-search_score', 'name')

        return queryset.order_by('name')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context