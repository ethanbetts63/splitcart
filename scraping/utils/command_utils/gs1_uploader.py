import os
import gzip
import requests
from .base_uploader import BaseUploader

class Gs1Uploader(BaseUploader):
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.outbox_path_name = 'gs1_outbox'
        self.archive_path_name = 'temp_jsonl_gs1_storage'
        self.upload_url_path = '/api/upload/gs1/'

    def run(self):
        outbox_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', self.outbox_path_name)
        archive_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', self.archive_path_name)
        os.makedirs(outbox_path, exist_ok=True)
        os.makedirs(archive_path, exist_ok=True)

        server_url = self.get_server_url()
        api_key = self.get_api_key()
        if not server_url or not api_key:
            return

        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {'X-API-KEY': api_key}

        files_to_upload = [f for f in os.listdir(outbox_path) if f.endswith('.jsonl')]

        if not files_to_upload:
            self.command.stdout.write(self.command.style.SUCCESS(f"No files to upload in {self.outbox_path_name}."))
            return

        for file_name in files_to_upload:
            file_path = os.path.join(outbox_path, file_name)
            compressed_file_path = file_path + '.gz'

            # 1. Compress the file
            try:
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_file_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                self.command.stdout.write(self.command.style.SUCCESS(f"Successfully compressed {file_name}"))
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Failed to compress {file_name}: {e}"))
                continue

            # 2. Upload the compressed file
            try:
                with open(compressed_file_path, 'rb') as f:
                    files = {'file': (os.path.basename(compressed_file_path), f)}
                    response = requests.post(upload_url, headers=headers, files=files, timeout=120)
                
                response.raise_for_status()  # Raise an exception for bad status codes

                self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded {file_name}"))

                # 3. Archive the original file
                archive_file_path = os.path.join(archive_path, file_name)
                os.rename(file_path, archive_file_path)
                self.command.stdout.write(self.command.style.SUCCESS(f"Archived {file_name}"))

            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"Failed to upload {file_name}: {e}"))
            finally:
                # 4. Clean up the compressed file
                if os.path.exists(compressed_file_path):
                    os.remove(compressed_file_path)
