import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from api.permissions import IsInternalAPIRequest

class StoreClustersFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed store_clusters .json files.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed store_clusters files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'store_clusters_inbox')
