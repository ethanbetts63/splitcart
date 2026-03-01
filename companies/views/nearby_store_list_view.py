from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from companies.serializers.store_serializer import StoreSerializer

class NearbyStoreListView(APIView):
    """
    API view to list stores within a given radius of a postcode.
    """
    def get(self, request, *args, **kwargs):
        postcode_param = request.query_params.get('postcode')
        radius_param = request.query_params.get('radius')
        companies_param = request.query_params.get('companies')

        if not postcode_param or not radius_param:
            return Response(
                {'error': 'Postcode and radius are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            radius = float(radius_param)
            postcode_list = [p.strip() for p in postcode_param.split(',')]
            all_nearby_stores = set()
            companies = companies_param.split(',') if companies_param else None

            for p_code in postcode_list:
                if not p_code: continue # Skip empty strings
                ref_postcode = Postcode.objects.filter(postcode=p_code).first()
                if ref_postcode:
                    nearby_stores = get_nearby_stores(ref_postcode, radius, companies=companies)
                    all_nearby_stores.update(nearby_stores)
            
            stores_list = list(all_nearby_stores)
            store_serializer = StoreSerializer(stores_list, many=True)
            return Response({'stores': store_serializer.data}, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {'error': 'Invalid radius.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
