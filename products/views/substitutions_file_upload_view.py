import os
import gzip
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from data_management.views.base_file_upload_view import BaseFileUploadView
from splitcart.permissions import IsInternalAPIRequest

class SubstitutionsFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed substitutions .json files.
    This view overrides the post method to de-duplicate substitutions before saving.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed substitutions files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'substitutions_inbox')

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        
        if not uploaded_file.name.endswith('.json.gz'):
            return Response({"error": "Invalid file format. Expected .json.gz"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decompress and save the file, assuming it's already de-duplicated
            inbox_path = self.get_inbox_path()
            os.makedirs(inbox_path, exist_ok=True)
            
            decompressed_file_name = uploaded_file.name.replace(".gz", "")
            decompressed_file_path = os.path.join(inbox_path, decompressed_file_name)

            with gzip.open(uploaded_file, 'rb') as f_in:
                with open(decompressed_file_path, 'wb') as f_out:
                    f_out.write(f_in.read())

            message = f"Successfully uploaded and saved '{decompressed_file_name}'."
            return Response({"message": message}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Failed to process file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
