from django.db.models import F, Subquery, OuterRef
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from products.models import Product, Bargain
from companies.models import StoreGroupMembership
from ...serializers import ProductSerializer

class BargainCarouselView(generics.ListAPIView):
    """
    An optimized view to serve products for the "Bargains" carousel.
    
    This view uses a "bargains-first" approach for performance. It finds a small
    set of top bargain products first, and then fetches the full product details,
    avoiding slow, large-scale annotations on the entire Product table.
    """
    permission_classes = [] # AllowAny
    serializer_class = ProductSerializer
    # No pagination needed for a carousel with a fixed limit
    pagination_class = None

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')

        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
            # We need to pass the store_ids to the serializer context
            self.nearby_store_ids = store_ids
        except (ValueError, TypeError):
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})

        # 1. Find the anchor stores for the user's selected stores.
        anchor_store_ids = list(StoreGroupMembership.objects.filter(
            store_id__in=store_ids
        ).values_list('group__anchor_id', flat=True).distinct())

        if not anchor_store_ids:
            return Product.objects.none()

        # 2. Find the IDs of the top ~40 unique products that have bargains
        #    strictly between the relevant anchor stores.
        top_product_ids = Bargain.objects.filter(
            cheaper_store_id__in=anchor_store_ids,
            expensive_store_id__in=anchor_store_ids
        ).order_by('-discount_percentage').values_list('product_id', flat=True).distinct()[:40]

        if not top_product_ids:
            return Product.objects.none()

        # 3. Now, run the annotation subquery on ONLY this small set of products.
        #    This is fast because the subquery runs on a tiny fraction of the product table.
        best_bargain_subquery = Bargain.objects.filter(
            product=OuterRef('pk'),
            cheaper_store_id__in=anchor_store_ids,
            expensive_store_id__in=anchor_store_ids
        ).order_by('-discount_percentage')

        queryset = Product.objects.filter(
            pk__in=list(top_product_ids)
        ).annotate(
            best_discount=Subquery(best_bargain_subquery.values('discount_percentage')[:1])
        ).order_by('-best_discount')[:20] # Final limit for the carousel

        return queryset.prefetch_related(
            'prices__store__company', 'skus', 'category__primary_category'
        ).defer('normalized_name_brand_size_variations', 'sizes')

    def get_serializer_context(self):
        """
        Passes the nearby_store_ids to the serializer.
        """
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context
