from django.db.models import Subquery, OuterRef
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from products.models import Product, Bargain
from ...serializers import ProductSerializer


class BargainCarouselView(generics.ListAPIView):
    """
    An optimized view to serve products for the "Bargains" carousel.
    
    This view uses a "bargains-first" approach for performance. It finds a small
    set of top bargain products first, and then fetches the full product details,
    avoiding slow, large-scale annotations on the entire Product table.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    # No pagination needed for a carousel with a fixed limit
    pagination_class = None

    @method_decorator(cache_page(60 * 60 * 24)) # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        store_ids_param = self.request.query_params.get('store_ids')
        company_id = self.request.query_params.get('company_id')
        try:
            limit = int(self.request.query_params.get('limit', 20))
        except (ValueError, TypeError):
            limit = 20
        
        # Enforce a reasonable maximum limit
        limit = min(limit, 100)

        if not store_ids_param:
            raise ValidationError({'store_ids': 'This field is required.'})

        try:
            store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
        except (ValueError, TypeError):
            raise ValidationError({'store_ids': 'Invalid format. Must be a comma-separated list of integers.'})

        # 1. The incoming store_ids are now pre-translated anchor IDs.
        # We can use them directly for all pricing and bargain logic.
        self.pricing_store_ids = store_ids # Store for serializer context

        if not self.pricing_store_ids:
            return Product.objects.none()

        # 2. Find the IDs of the top unique products that have bargains
        #    strictly between the relevant pricing stores. Fetch more to ensure we have enough unique products.
        initial_fetch_limit = limit * 2
        bargain_query = Bargain.objects.filter(
            cheaper_store_id__in=self.pricing_store_ids,
            expensive_store_id__in=self.pricing_store_ids
        )

        # Optional: Filter by a specific company's bargains
        if company_id:
            bargain_query = bargain_query.filter(cheaper_store__company_id=company_id)
        
        top_product_ids = bargain_query.order_by(
            '-discount_percentage'
        ).values_list('product_id', flat=True).distinct()[:initial_fetch_limit]


        if not top_product_ids:
            return Product.objects.none()

        # 3. Now, run the annotation subquery on ONLY this small set of products.
        #    The subquery must also respect the definitive pricing_store_ids.
        best_bargain_subquery = Bargain.objects.filter(
            product=OuterRef('pk'),
            cheaper_store_id__in=self.pricing_store_ids,
            expensive_store_id__in=self.pricing_store_ids
        )
        if company_id:
            best_bargain_subquery = best_bargain_subquery.filter(cheaper_store__company_id=company_id)
        
        best_bargain_subquery = best_bargain_subquery.order_by('-discount_percentage')


        queryset = Product.objects.filter(
            pk__in=list(top_product_ids)
        ).annotate(
            best_discount=Subquery(best_bargain_subquery.values('discount_percentage')[:1]),
            cheaper_store_name=Subquery(best_bargain_subquery.values('cheaper_store__store_name')[:1]),
            cheaper_company_name=Subquery(best_bargain_subquery.values('cheaper_store__company__name')[:1])
        ).order_by('-best_discount')[:limit] # Final limit for the carousel

        return queryset.prefetch_related(
            'prices__store__company', 'skus', 'category__primary_category'
        ).defer('normalized_name_brand_size_variations', 'sizes')

    def get_serializer_context(self):
        """
        Passes the pricing_store_ids to the serializer.
        """
        context = super().get_serializer_context()
        # Use 'nearby_store_ids' as the key because the serializer already expects it.
        context['nearby_store_ids'] = getattr(self, 'pricing_store_ids', None)
        return context
