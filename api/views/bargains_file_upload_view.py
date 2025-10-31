import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from api.permissions import IsInternalAPIRequest

class BargainsFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed bargains .json files.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed bargains files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox')
