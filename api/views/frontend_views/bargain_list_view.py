from django.views.decorators.cache import cache_page # New import
from django.utils.decorators import method_decorator # New import
from rest_framework import generics
from rest_framework.permissions import AllowAny
from products.models import Product, Bargain
from ...serializers import ProductSerializer

@method_decorator(cache_page(3600), name='dispatch') # Apply cache_page decorator
class BargainListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')
        super_category_param = self.request.query_params.get('super_category')

        if not store_ids_param:
            return Product.objects.none()

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            
            bargain_queryset = Bargain.objects.filter(store__id__in=store_ids)

            if super_category_param:
                bargain_queryset = bargain_queryset.filter(super_categories__name=super_category_param)

            product_ids = bargain_queryset.values_list('product_id', flat=True).distinct()
            
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
