import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from api.permissions import IsInternalAPIRequest

class BargainFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of the compressed bargains.json.gz file from the scraper.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed bargains file.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox')
