from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from ..serializers import StoreSerializer

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
            ref_postcode = Postcode.objects.filter(postcode=postcode_param).first()

            if ref_postcode:
                companies = companies_param.split(',') if companies_param else None
                nearby_stores = get_nearby_stores(ref_postcode, radius, companies=companies)
                serializer = StoreSerializer(nearby_stores, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Invalid postcode.'},
                    status=status.HTTP_404_NOT_FOUND
                )

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
