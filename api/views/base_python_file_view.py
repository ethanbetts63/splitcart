from django.http import HttpResponse, JsonResponse
from django.views import View
import hashlib

class BasePythonFileView(View):
    """
    A base view for generating and serving a Python file containing a dictionary.
    Handles ETag-based caching.
    """
    generator_class = None
    variable_name = None

    def get(self, request, *args, **kwargs):
        if not self.generator_class or not self.variable_name:
            return JsonResponse({"error": "View not configured"}, status=500)

        # 1. Generate the data dictionary
        generator = self.generator_class()
        data_dict = generator.generate_translation_dict()

        # 2. Format as a Python file string
        file_content = f'# This file is auto-generated. Do not edit.\n\n{self.variable_name} = {data_dict}\n'
        file_bytes = file_content.encode('utf-8')

        # 3. Calculate ETag and check against client's version
        etag = f'"' + hashlib.md5(file_bytes).hexdigest() + f'"'
        if request.headers.get('If-None-Match') == etag:
            return HttpResponse(status=304)

        # 4. Create and return the response
        response = HttpResponse(file_content, content_type='text/plain')
        response['ETag'] = etag
        return response
