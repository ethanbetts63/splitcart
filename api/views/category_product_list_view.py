from rest_framework import generics
from django.db.models import Exists, OuterRef
from products.models import Product, Bargain
from ..serializers import ProductSerializer
from companies.models import Category

class CategoryProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        primary_category_slug = self.request.query_params.get('primary_category_slug', None)
        store_ids_param = self.request.query_params.get('store_ids')

        if not primary_category_slug:
            return Product.objects.none()

        try:
            store_ids = []
            if store_ids_param:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
                # Store ids for the serializer context to fetch correct prices
                self.nearby_store_ids = store_ids

            # Base queryset
            queryset = Product.objects.filter(category__primary_category__slug=primary_category_slug)

            # Further filter by selected stores if store_ids are provided.
            if store_ids:
                queryset = queryset.filter(
                    price_records__price_entries__store__id__in=store_ids
                ).distinct()

            # Annotate with bargain status within the selected stores
            bargain_exists = Bargain.objects.filter(
                product=OuterRef('pk'),
                store__id__in=store_ids
            )
            queryset = queryset.annotate(
                is_bargain=Exists(bargain_exists)
            )

            # Order by bargain status first, then by name
            queryset = queryset.order_by('-is_bargain', 'name')

            return queryset

        except (ValueError, TypeError):
            return Product.objects.none()

    def get_serializer_context(self):
        # Pass store_ids to the serializer context
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', [])
        return context
