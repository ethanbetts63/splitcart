
import os
import json
import requests
from django.conf import settings

class SubstitutionsUploader:
    def __init__(self, command):
        self.command = command
        self.outbox_path_name = 'data_management/data/substitutions_outbox'
        self.archive_path_name = 'data_management/data/substitutions_archive'
        self.upload_url_path = '/api/import/semantic_data/'
        self.file_name = 'substitutions.json'
        self.chunk_size = 2000  # Process 2000 substitutions per request

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
                all_substitutions = json.load(f)
            
            total_subs = len(all_substitutions)
            total_chunks = (total_subs + self.chunk_size - 1) // self.chunk_size

            self.command.stdout.write(f"Beginning upload of {total_subs} substitutions in {total_chunks} chunks...")

            for i in range(0, total_subs, self.chunk_size):
                chunk = all_substitutions[i:i + self.chunk_size]
                payload = {'substitutions': chunk}
                
                self.command.stdout.write(f"  Uploading chunk {i // self.chunk_size + 1} of {total_chunks} ({len(chunk)} substitutions)...", ending='')

                response = requests.post(upload_url, headers=headers, json=payload, timeout=180) # 3 min timeout per chunk
                response.raise_for_status()
                
                self.command.stdout.write(self.command.style.SUCCESS(" Done."))

            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded all {total_subs} substitutions."))

            # Archive the file after all chunks are successfully uploaded
            archive_file_path = os.path.join(archive_path, self.file_name)
            os.rename(file_path, archive_file_path)
            self.command.stdout.write(self.command.style.SUCCESS(f"Archived {self.file_name}."))

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nFailed to upload chunk: {e}"))
        except FileNotFoundError:
            self.command.stderr.write(self.command.style.ERROR(f"File not found: {file_path}"))
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_name}"))
