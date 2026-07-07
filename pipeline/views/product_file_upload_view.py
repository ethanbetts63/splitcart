import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from config.permissions import IsInternalAPIRequest

class ProductFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed product .jsonl files from the scraper.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed product files.
        """
        return os.fspath(settings.PIPELINE_DATA_DIR / 'inboxes' / 'product_inbox')
