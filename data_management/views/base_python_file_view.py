from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from splitcart.permissions import IsInternalAPIRequest
import hashlib

class BasePythonFileView(APIView):
    """
    A base view for generating and serving a Python file containing a dictionary.
    Handles ETag-based caching.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    generator_class = None
    variable_name = None

    def get(self, request, *args, **kwargs):
        if not self.generator_class:
            return JsonResponse({"error": "View not configured"}, status=500)

        # 1. Get the path to the file from the generator class
        # We instantiate the generator only to get its configured output_path
        generator = self.generator_class()
        file_path = generator.output_path

        # 2. Read the file from the disk
        try:
            with open(file_path, 'rb') as f: # Read as bytes for hashing
                file_bytes = f.read()
        except FileNotFoundError:
            return JsonResponse({"error": f"Translation file not found at {file_path}. Please run the 'update' command to generate it."}, status=404)

        # 3. Calculate ETag and check against client's version
        etag = f'"' + hashlib.md5(file_bytes).hexdigest() + f'"'
        if request.headers.get('If-None-Match') == etag:
            return HttpResponse(status=304)

        # 4. Create and return the response
        response = HttpResponse(file_bytes, content_type='text/plain')
        response['ETag'] = etag
        return response
