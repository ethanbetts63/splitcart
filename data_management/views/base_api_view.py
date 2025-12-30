from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from splitcart.permissions import IsInternalAPIRequest

class BaseAPIView(APIView):
    """
    A base view that enforces API key authentication for all incoming requests.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'
