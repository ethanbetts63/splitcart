from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from data_management.models import BargainStats
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

#@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
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
