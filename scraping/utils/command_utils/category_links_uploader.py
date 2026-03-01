import os
import gzip
import requests
from django.conf import settings
from .base_uploader import BaseUploader

class CategoryLinksUploader(BaseUploader):
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.outbox_path_name = 'data_management/data/outboxes/category_links_outbox'
        self.upload_url_path = '/api/upload/category-links/'
        self.file_name = 'category_links.json'

    def run(self):
        outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'category_links_outbox')
        file_path = os.path.join(outbox_path, self.file_name)

        if not os.path.exists(file_path):
            self.command.stdout.write(self.command.style.SUCCESS(f"No file to upload in {self.outbox_path_name}."))
            return

        server_url = self.get_server_url()
        api_key = self.get_api_key()
        if not server_url or not api_key:
            return

        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {'X-Internal-API-Key': api_key}

        compressed_file_path = file_path + '.gz'

        # 1. Compress the file
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_file_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully compressed {self.file_name}"))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to compress {self.file_name}: {e}"))
            return

        # 2. Upload the compressed file
        try:
            with open(compressed_file_path, 'rb') as f:
                files = {'file': (os.path.basename(compressed_file_path), f)}
                response = requests.post(upload_url, headers=headers, files=files, timeout=120)
            
            response.raise_for_status()

            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded {self.file_name}"))

            # 3. Delete the original file
            os.remove(file_path)

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to upload {self.file_name}: {e}"))
        finally:
            # 4. Clean up the compressed file
            if os.path.exists(compressed_file_path):
                os.remove(compressed_file_path)