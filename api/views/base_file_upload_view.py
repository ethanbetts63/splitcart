import gzip
import os
import hmac
from abc import ABC, abstractmethod
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

class BaseFileUploadView(APIView, ABC):
    """
    An abstract base view for handling the upload of compressed .jsonl files.
    It handles authentication, decompression, and file saving, while delegating
    the final destination path to subclasses.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    def post(self, request, *args, **kwargs):
        # 2. Process the uploaded file
        if 'file' not in request.FILES:
            return Response({"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name

        if not file_name.endswith(('.jsonl.gz', '.json.gz')):
            return Response({"error": "Invalid file format. Expected .jsonl.gz"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Decompress and save the file
        try:
            inbox_path = self.get_inbox_path()
            os.makedirs(inbox_path, exist_ok=True)
            
            decompressed_file_name = file_name.replace(".gz", "")
            decompressed_file_path = os.path.join(inbox_path, decompressed_file_name)

            with gzip.open(uploaded_file, 'rb') as f_in:
                with open(decompressed_file_path, 'wb') as f_out:
                    f_out.write(f_in.read())

        except Exception as e:
            return Response({"error": f"Failed to process file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"Successfully uploaded and decompressed '{decompressed_file_name}'"}, status=status.HTTP_201_CREATED)

    @abstractmethod
    def get_inbox_path(self) -> str:
        """
        Abstract method that must be implemented by subclasses to provide the
        destination directory for the decompressed file.
        """
        pass
