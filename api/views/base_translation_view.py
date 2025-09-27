import json
import gzip
import hashlib
from django.http import HttpResponse, JsonResponse
from django.views import View

class BaseTranslationView(View):
    """
    A base view for generating and serving translation table data.

    This view handles the common logic for:
    - Instantiating a data generator class.
    - Generating a dictionary of data.
    - Calculating an ETag hash to support client-side caching.
    - Compressing the response with gzip.
    - Returning a 304 Not Modified response if the client's version is current.
    """
    generator_class = None

    def get(self, request, *args, **kwargs):
        if not self.generator_class:
            return JsonResponse({"error": "Generator class not specified"}, status=500)

        # 1. Generate the data dictionary
        generator = self.generator_class()
        data_dict = generator.generate_translation_dict()
        
        # 2. Create a JSON string and calculate its ETag
        json_data = json.dumps(data_dict, sort_keys=True).encode('utf-8')
        etag = f'"' + hashlib.md5(json_data).hexdigest() + f'"'

        # 3. Check against client's ETag
        if request.headers.get('If-None-Match') == etag:
            return HttpResponse(status=304)

        # 4. Compress the data for transmission
        compressed_data = gzip.compress(json_data)

        # 5. Create the response
        response = HttpResponse(compressed_data, content_type='application/json')
        response['Content-Encoding'] = 'gzip'
        response['ETag'] = etag
        
        return response
