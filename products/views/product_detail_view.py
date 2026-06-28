from rest_framework.generics import RetrieveAPIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from products.models import Product
from products.serializers.product_serializer import ProductSerializer
@method_decorator(cache_page(60 * 30), name='dispatch')
class ProductDetailView(RetrieveAPIView):
    """
    API view to retrieve a single product by its ID.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        """
        Adds the correct store IDs for pricing to the serializer context.
        """
        context = super().get_serializer_context()
        store_ids_param = self.request.query_params.get('store_ids')

        if store_ids_param:
            try:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
                context['nearby_store_ids'] = store_ids
            except (ValueError, TypeError):
                context['nearby_store_ids'] = []
        else:
            context['nearby_store_ids'] = []
            
        return context
