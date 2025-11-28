from rest_framework.generics import RetrieveAPIView
from products.models import Product
from ...serializers import ProductSerializer
from ...utils.get_pricing_stores import get_pricing_stores

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
                # Use the helper to get the final list of stores for pricing
                context['nearby_store_ids'] = get_pricing_stores(store_ids)
            except (ValueError, TypeError):
                # Fail gracefully if store_ids are invalid
                context['nearby_store_ids'] = []
        else:
            context['nearby_store_ids'] = []
            
        return context
