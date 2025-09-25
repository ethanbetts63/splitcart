import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView

class StoreFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed store .jsonl files.
    """
    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed store files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'store_inbox')
