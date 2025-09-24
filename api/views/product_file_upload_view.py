import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView

class ProductFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed product .jsonl files from the scraper.
    """
    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed product files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'product_inbox')