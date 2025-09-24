import os
import gzip
import requests
from django.conf import settings

class ProductUploader:
    def __init__(self, command):
        self.command = command
        self.outbox_path_name = 'product_outbox'
        self.archive_path_name = 'temp_jsonl_product_storage'
        self.upload_url_path = '/api/upload/products/'

    def run(self):
        outbox_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', self.outbox_path_name)
        archive_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', self.archive_path_name)
        os.makedirs(outbox_path, exist_ok=True)
        os.makedirs(archive_path, exist_ok=True)

        try:
            server_url = settings.API_SERVER_URL
            api_key = settings.API_SECRET_KEY
        except AttributeError:
            self.command.stderr.write(self.command.style.ERROR("API_SERVER_URL and API_SECRET_KEY must be configured in settings."))
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
