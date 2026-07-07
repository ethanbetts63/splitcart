import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from config.permissions import IsInternalAPIRequest

class CategoryLinksFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed category links .json files.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed category links files.
        """
        return os.fspath(settings.PIPELINE_DATA_DIR / 'inboxes' / 'category_links_inbox')
