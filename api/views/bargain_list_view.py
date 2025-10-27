from django.views.decorators.cache import cache_page # New import
from django.utils.decorators import method_decorator # New import
from rest_framework import generics
from rest_framework.permissions import AllowAny
from products.models import Product, Bargain
from ..serializers import ProductSerializer

@method_decorator(cache_page(3600), name='dispatch') # Apply cache_page decorator
class BargainListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')
        if not store_ids_param:
            return Product.objects.none()  # Return nothing if no stores are selected

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            # Get unique product IDs from the Bargain table that match the user's stores
            product_ids = Bargain.objects.filter(store__id__in=store_ids).values_list('product_id', flat=True).distinct()
            
            # Fetch the actual Product objects for those IDs
            # We can also order them by the bargain's percentage difference if we want
            # For now, just getting the products is fine.
            queryset = Product.objects.filter(id__in=product_ids)
            return queryset
        except (ValueError, TypeError):
            return Product.objects.none()

    def get_serializer_context(self):
        # Pass nearby_store_ids to the serializer, similar to ProductListView
        context = super().get_serializer_context()
        store_ids_param = self.request.query_params.get('store_ids')
        if store_ids_param:
            try:
                context['nearby_store_ids'] = [int(s_id) for s_id in store_ids_param.split(',')]
            except (ValueError, TypeError):
                pass
        return context
