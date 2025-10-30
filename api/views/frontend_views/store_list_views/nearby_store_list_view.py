from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from api.serializers import StoreSerializer

class StoreListView(APIView):
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
            
            serializer = StoreSerializer(list(all_nearby_stores), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

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
