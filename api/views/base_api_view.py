import hmac
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView

class BaseAPIView(APIView):
    """
    A base view that enforces API key authentication for all incoming requests.
    """
    def dispatch(self, request, *args, **kwargs):
        # 1. Authenticate the request
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return JsonResponse({"error": "API key missing."}, status=401)

        try:
            secret_key = settings.API_SECRET_KEY
        except AttributeError:
            return JsonResponse({"error": "API_SECRET_KEY not configured on server."}, status=500)

        if not hmac.compare_digest(api_key, secret_key):
            return JsonResponse({"error": "Invalid API key."}, status=401)

        # If authentication is successful, proceed to the actual view method (e.g., get, post)
        return super().dispatch(request, *args, **kwargs)
