import gzip
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import hmac

class FileUploadView(APIView):
    """
    A view to handle the upload of compressed .jsonl files from the scraper.
    """
    def post(self, request, *args, **kwargs):
        # 1. Authenticate the request
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return Response({"error": "API key missing."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            secret_key = settings.API_SECRET_KEY
        except AttributeError:
            return Response({"error": "API_SECRET_KEY not configured on server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not hmac.compare_digest(api_key, secret_key):
            return Response({"error": "Invalid API key."}, status=status.HTTP_401_UNAUTHORIZED)

        # 2. Process the uploaded file
        if 'file' not in request.FILES:
            return Response({"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name

        # Expecting a .jsonl.gz file
        if not file_name.endswith('.jsonl.gz'):
            return Response({"error": "Invalid file format. Expected .jsonl.gz"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Decompress and save the file
        try:
            inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'product_inbox')
            os.makedirs(inbox_path, exist_ok=True)
            
            decompressed_file_name = file_name[:-3]  # Remove .gz extension
            decompressed_file_path = os.path.join(inbox_path, decompressed_file_name)

            with gzip.open(uploaded_file, 'rb') as f_in:
                with open(decompressed_file_path, 'wb') as f_out:
                    f_out.write(f_in.read())

        except Exception as e:
            return Response({"error": f"Failed to process file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"Successfully uploaded and decompressed '{decompressed_file_name}'"}, status=status.HTTP_201_CREATED)
