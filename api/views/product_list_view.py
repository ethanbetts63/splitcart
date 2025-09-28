
from rest_framework import generics, filters
from products.models import Product
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from ..serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Product.objects.all().order_by('name')
        postcode_param = self.request.query_params.get('postcode')
        radius_param = self.request.query_params.get('radius')

        if postcode_param and radius_param:
            try:
                radius = float(radius_param)
                # Assuming a single postcode for now, can be extended to multiple
                ref_postcode = Postcode.objects.filter(postcode=postcode_param).first()

                if ref_postcode:
                    nearby_stores = get_nearby_stores(ref_postcode, radius)
                    nearby_store_ids = [store.id for store in nearby_stores]
                    
                    # Filter products that have prices in these nearby stores
                    queryset = queryset.filter(price_records__price_entries__store__id__in=nearby_store_ids).distinct()
                else:
                    # If postcode not found, return empty queryset or all products
                    queryset = Product.objects.none() # Or return all products if preferred
            except (ValueError, TypeError):
                pass # Invalid radius, ignore filtering

        return queryset
