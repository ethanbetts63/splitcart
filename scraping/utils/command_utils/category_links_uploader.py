
import os
import json
import requests
from django.conf import settings

class CategoryLinksUploader:
    def __init__(self, command):
        self.command = command
        self.outbox_path_name = 'data_management/data/category_links_outbox'
        self.archive_path_name = 'data_management/data/category_links_archive' # New archive dir
        self.upload_url_path = '/api/import/semantic_data/'
        self.file_name = 'category_links.json'

    def run(self):
        outbox_path = os.path.join(settings.BASE_DIR, self.outbox_path_name)
        archive_path = os.path.join(settings.BASE_DIR, self.archive_path_name)
        os.makedirs(archive_path, exist_ok=True)

        file_path = os.path.join(outbox_path, self.file_name)

        if not os.path.exists(file_path):
            self.command.stdout.write(self.command.style.SUCCESS(f"No file to upload in {self.outbox_path_name}."))
            return

        try:
            server_url = settings.API_SERVER_URL
            api_key = settings.API_SECRET_KEY
        except AttributeError:
            self.command.stderr.write(self.command.style.ERROR("API_SERVER_URL and API_SECRET_KEY must be configured in settings."))
            return

        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        try:
            with open(file_path, 'r') as f:
                data_to_upload = json.load(f)
            
            # The import endpoint expects a top-level key
            payload = {'category_links': data_to_upload}

            response = requests.post(upload_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded {self.file_name}."))
            self.command.stdout.write(str(response.json()))

            # Archive the file
            archive_file_path = os.path.join(archive_path, self.file_name)
            os.rename(file_path, archive_file_path)
            self.command.stdout.write(self.command.style.SUCCESS(f"Archived {self.file_name}."))

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to upload {self.file_name}: {e}"))
        except FileNotFoundError:
            self.command.stderr.write(self.command.style.ERROR(f"File not found: {file_path}"))
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_name}"))
