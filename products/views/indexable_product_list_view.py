from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView

from products.serializers.product_serializer import IndexableProductSerializer
from products.utils.indexable import indexable_products


@method_decorator(cache_page(60 * 60), name='dispatch')
class IndexableProductListView(ListAPIView):
    """
    The product pages the sitemap lists: every product `indexable_products`
    admits, unpaginated, because the sitemap is one document and one fetch per
    revalidation is cheaper than walking pages of it.
    """

    throttle_scope = 'public'
    serializer_class = IndexableProductSerializer
    pagination_class = None

    def get_queryset(self):
        return indexable_products().only('id', 'name').order_by('id')
