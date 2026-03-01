import os
import gzip
import json
import requests
from django.conf import settings
from .base_uploader import BaseUploader
from data_management.utils.deduplication_utils.substitution_deduplicator import deduplicate_substitutions


class SubstitutionsUploader(BaseUploader):
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.outbox_path_name = 'data_management/data/outboxes/substitutions_outbox'
        self.upload_url_path = '/api/upload/substitutions/'
        self.file_name = 'substitutions.json'

    def run(self):
        outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'substitutions_outbox')
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

        try:
            # 1. Read and de-duplicate the data
            with open(file_path, 'r', encoding='utf-8') as f:
                subs_data = json.load(f)
            
            deduplicated_subs = deduplicate_substitutions(subs_data)
            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully de-duplicated substitutions. Original: {len(subs_data)}, Final: {len(deduplicated_subs)}"))

            # 2. Compress the de-duplicated data in memory
            json_string = json.dumps(deduplicated_subs)
            compressed_data = gzip.compress(json_string.encode('utf-8'))
            
            # 3. Upload the compressed in-memory data
            compressed_filename = self.file_name + '.gz'
            files = {'file': (compressed_filename, compressed_data, 'application/gzip')}
            
            self.command.stdout.write(f"Uploading {compressed_filename}...")
            response = requests.post(upload_url, headers=headers, files=files, timeout=120)
            response.raise_for_status()

            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded {self.file_name}"))

            # 4. Delete the original file after successful upload
            os.remove(file_path)

        except FileNotFoundError:
            self.command.stderr.write(self.command.style.ERROR(f"File not found: {file_path}"))
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to decode JSON from {file_path}"))
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to upload {self.file_name}: {e}"))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred: {e}"))