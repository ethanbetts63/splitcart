import os
import gzip
import requests
from django.conf import settings
from .base_uploader import BaseUploader

class BargainUploader(BaseUploader):
    """
    Handles the upload of the generated bargains file to the API endpoint.
    """
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.source_file = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'bargains_outbox', 'bargains.json')
        self.upload_url_path = '/api/upload/bargains/'

    def run(self):
        """
        Executes the file upload operation.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Uploading Bargains via API ---"))
        if not os.path.exists(self.source_file):
            self.command.stdout.write(self.command.style.WARNING(f"  - No bargain file found at {self.source_file}. Nothing to upload."))
            return

        server_url = self.get_server_url()
        api_key = self.get_api_key()
        if not server_url or not api_key:
            return

        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {'X-Internal-API-Key': api_key}
        compressed_file_path = self.source_file + '.gz'

        try:
            # 1. Gzip the file
            self.command.stdout.write(f"  - Compressing {os.path.basename(self.source_file)}...")
            with open(self.source_file, 'rb') as f_in, gzip.open(compressed_file_path, 'wb') as f_out:
                f_out.writelines(f_in)
            self.command.stdout.write(f"    - Compression complete.")

            # 2. Upload the compressed file
            self.command.stdout.write(f"  - Uploading to {upload_url}...")
            with open(compressed_file_path, 'rb') as f:
                files = {'file': (os.path.basename(compressed_file_path), f)}
                response = requests.post(upload_url, headers=headers, files=files, timeout=120)
                response.raise_for_status()

            # 3. Cleanup on success
            self.command.stdout.write(self.command.style.SUCCESS("  - Upload successful."))
            if os.path.exists(self.source_file):
                os.remove(self.source_file)
            if os.path.exists(compressed_file_path):
                os.remove(compressed_file_path)
            self.command.stdout.write(f"  - Cleanup complete.")

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"  - An error occurred during upload: {e}"))
            if hasattr(e, 'response') and e.response is not None:
                self.command.stderr.write(f"    - Response body: {e.response.text}")
            # Do not clean up files on failure, so it can be retried
            raise
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"  - An unexpected error occurred: {e}"))
            # Do not clean up files on failure
            raise
