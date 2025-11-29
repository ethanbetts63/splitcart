from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from data_management.models import BargainStats

class BargainStatsView(APIView):
    """
    API view to retrieve pre-calculated bargain statistics.
    """
    def get(self, request, *args, **kwargs):
        try:
            # We are fetching a specific, single object
            stats_object = BargainStats.objects.get(key='company_bargain_comparison')
            # We only want to return the JSON data field
            return Response(stats_object.data)
        except BargainStats.DoesNotExist:
            return Response(
                {"detail": "Bargain statistics not found. Please run the calculation command."},
                status=status.HTTP_404_NOT_FOUND
            )
