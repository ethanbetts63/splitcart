import os
import gzip
import requests
from django.conf import settings
from .base_uploader import BaseUploader

class BargainUploader(BaseUploader):
    """
    Handles the upload of all generated bargain files from the outbox directory.
    """
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.source_dir = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'bargains_outbox')
        self.upload_url_path = '/api/upload/bargains/'

    def run(self):
        """
        Executes the file upload operation for all .json files in the source directory.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Uploading Bargains via API ---"))
        
        if not os.path.exists(self.source_dir):
            self.command.stdout.write(self.command.style.WARNING(f"  - Bargain directory not found at {self.source_dir}. Nothing to upload."))
            return

        # Find all .json files in the directory
        try:
            files_to_upload = sorted([f for f in os.listdir(self.source_dir) if f.endswith('.json')])
        except FileNotFoundError:
            self.command.stdout.write(self.command.style.WARNING(f"  - Bargain directory not found at {self.source_dir}. Nothing to upload."))
            return

        if not files_to_upload:
            self.command.stdout.write(self.command.style.WARNING(f"  - No .json bargain files found in {self.source_dir}. Nothing to upload."))
            return
            
        self.command.stdout.write(f"  - Found {len(files_to_upload)} bargain files to upload.")

        server_url = self.get_server_url()
        api_key = self.get_api_key()
        if not server_url or not api_key:
            return
        
        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {'X-Internal-API-Key': api_key}
        
        for filename in files_to_upload:
            source_file_path = os.path.join(self.source_dir, filename)
            compressed_file_path = source_file_path + '.gz'
            self.command.stdout.write(f"\n--- Processing file: {filename} ---")

            try:
                # 1. Gzip the file
                self.command.stdout.write(f"  - Compressing {filename}...")
                with open(source_file_path, 'rb') as f_in, gzip.open(compressed_file_path, 'wb') as f_out:
                    f_out.writelines(f_in)
                self.command.stdout.write(f"    - Compression complete.")

                # 2. Upload the compressed file
                self.command.stdout.write(f"  - Uploading to {upload_url}...")
                with open(compressed_file_path, 'rb') as f:
                    files = {'file': (os.path.basename(compressed_file_path), f)}
                    response = requests.post(upload_url, headers=headers, files=files, timeout=300) # Increased timeout for larger files
                    response.raise_for_status()

                # 3. Cleanup on success
                self.command.stdout.write(self.command.style.SUCCESS("  - Upload successful."))
                if os.path.exists(source_file_path):
                    os.remove(source_file_path)
                if os.path.exists(compressed_file_path):
                    os.remove(compressed_file_path)
                self.command.stdout.write(f"  - Cleanup complete.")

            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"  - An error occurred during upload of {filename}: {e}"))
                if hasattr(e, 'response') and e.response is not None:
                    self.command.stderr.write(f"    - Response body: {e.response.text}")
                # Stop the whole process on failure so it can be retried without losing files
                self.command.stderr.write(self.command.style.ERROR("Aborting upload process due to error."))
                raise
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"  - An unexpected error occurred with {filename}: {e}"))
                self.command.stderr.write(self.command.style.ERROR("Aborting upload process due to error."))
                raise
