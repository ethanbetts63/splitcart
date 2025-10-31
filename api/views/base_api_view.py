from rest_framework.views import APIView
from api.permissions import IsInternalAPIRequest

class BaseAPIView(APIView):
    """
    A base view that enforces API key authentication for all incoming requests.
    """
    permission_classes = [IsInternalAPIRequest]
