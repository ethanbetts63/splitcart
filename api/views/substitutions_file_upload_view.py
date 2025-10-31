import os
from django.conf import settings
from .base_file_upload_view import BaseFileUploadView
from api.permissions import IsInternalAPIRequest

class SubstitutionsFileUploadView(BaseFileUploadView):
    """
    A view to handle the upload of compressed substitutions .json files.
    """
    permission_classes = [IsInternalAPIRequest]

    def get_inbox_path(self) -> str:
        """
        Returns the destination directory for the decompressed substitutions files.
        """
        return os.path.join(settings.BASE_DIR, 'data_management', 'data', 'substitutions_inbox')
