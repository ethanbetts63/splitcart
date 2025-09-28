
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

        print(f"DEBUG: Postcode param: {postcode_param}, Radius param: {radius_param}")

        if postcode_param and radius_param:
            try:
                radius = float(radius_param)
                # Assuming a single postcode for now, can be extended to multiple
                ref_postcode = Postcode.objects.filter(postcode=postcode_param).first()
                print(f"DEBUG: Reference Postcode: {ref_postcode}")

                if ref_postcode:
                    nearby_stores = get_nearby_stores(ref_postcode, radius)
                    nearby_store_ids = [store.id for store in nearby_stores]
                    print(f"DEBUG: Nearby Stores ({len(nearby_stores)}): {[s.store_name for s in nearby_stores]}")
                    print(f"DEBUG: Nearby Store IDs: {nearby_store_ids}")
                    
                    # Filter products that have prices in these nearby stores
                    initial_queryset_count = queryset.count()
                    print(f"DEBUG: Queryset count before filter: {initial_queryset_count}, after filter: {queryset.count()}")
                    self.nearby_store_ids = nearby_store_ids # Store for serializer context
                else:
                    print(f"DEBUG: Postcode {postcode_param} not found.")
                    queryset = Product.objects.none()
            except (ValueError, TypeError) as e:
                print(f"DEBUG: Error in radius or postcode: {e}")
                pass # Invalid radius, ignore filtering

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['nearby_store_ids'] = getattr(self, 'nearby_store_ids', None)
        return context
