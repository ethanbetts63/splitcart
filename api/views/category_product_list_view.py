from rest_framework import generics
from django.db.models import Count
from products.models import Product
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
            # Filter products that belong to any category linked to the primary category.
            queryset = Product.objects.filter(category__primary_category__slug=primary_category_slug)

            # Further filter by selected stores if store_ids are provided.
            if store_ids_param:
                store_ids = [int(s_id) for s_id in store_ids_param.split(',')]
                queryset = queryset.filter(
                    price_records__price_entries__store__id__in=store_ids
                ).distinct()
                # Store ids for the serializer context to fetch correct prices
                self.nearby_store_ids = store_ids
            
            # Filter for bargains if requested
            bargains_param = self.request.query_params.get('bargains', 'false')
            if bargains_param.lower() == 'true':
                queryset = queryset.filter(price_records__price_entries__is_on_special=True).distinct()

            # Keep default ordering for now as per user's request
            return queryset

        except (ValueError, TypeError):
            return Product.objects.none()

        except (ValueError, TypeError):
            return Product.objects.none()

    def get_serializer_context(self):
        # Pass store_ids to the serializer context
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', [])
        return context
