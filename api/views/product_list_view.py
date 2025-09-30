
from rest_framework import generics, filters
from products.models import Product
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'brand__name', 'size']

    def get_queryset(self):
        queryset = Product.objects.all().order_by('name')
        store_ids_param = self.request.query_params.get('store_ids')

        if store_ids_param:
            try:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
                # Filter products that have prices in any of the specified stores
                queryset = queryset.filter(
                    price_records__price_entries__store__id__in=store_ids
                ).distinct()
                self.nearby_store_ids = store_ids # Store for serializer context
            except (ValueError, TypeError) as e:
                pass # Invalid store_ids, ignore filtering

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context
