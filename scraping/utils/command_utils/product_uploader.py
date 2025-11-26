import os
import gzip
import json
import requests
from datetime import datetime
from django.conf import settings
from .base_uploader import BaseUploader
from scraping.utils.command_utils.sanity_checker import run_sanity_checks

class ProductUploader(BaseUploader):
    def __init__(self, command, dev=False):
        super().__init__(command, dev)
        self.outbox_path_name = 'product_outbox'
        self.archive_path_name = 'temp_jsonl_product_storage'
        self.upload_url_path = '/api/upload/products/'

    def run(self):
        outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', self.outbox_path_name)
        archive_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', self.archive_path_name)
        os.makedirs(outbox_path, exist_ok=True)
        os.makedirs(archive_path, exist_ok=True)

        server_url = self.get_server_url()
        api_key = self.get_api_key()
        if not server_url or not api_key:
            return

        upload_url = f"{server_url.rstrip('/')}/{self.upload_url_path.lstrip('/')}"
        headers = {'X-Internal-API-Key': api_key}

        all_files = [f for f in os.listdir(outbox_path) if f.endswith('.jsonl')]

        if not all_files:
            self.command.stdout.write(self.command.style.SUCCESS(f"No files to upload in {self.outbox_path_name}."))
            return

        # Identify the most recent file for each store
        latest_files_per_store = {}
        for file_name in all_files:
            file_path = os.path.join(outbox_path, file_name)
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline()
                    if not first_line:
                        self.command.stdout.write(self.command.style.WARNING(f"File {file_name} is empty, skipping."))
                        continue
                    data = json.loads(first_line)
                    store_id = data.get('metadata', {}).get('store_id')
                    scraped_date_str = data.get('metadata', {}).get('scraped_date')

                    if not store_id or not scraped_date_str:
                        self.command.stdout.write(self.command.style.WARNING(f"Could not find store_id or scraped_date in {file_name}, skipping."))
                        continue
                    
                    scraped_date = datetime.strptime(scraped_date_str, '%Y-%m-%d').date()

                    if store_id not in latest_files_per_store or scraped_date > latest_files_per_store[store_id]['scraped_date']:
                        latest_files_per_store[store_id] = {
                            'file_name': file_name,
                            'scraped_date': scraped_date
                        }
            except (json.JSONDecodeError, IOError) as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error processing {file_name} to determine recency: {e}"))
                # If we can't process it, we can't determine if it's the latest. It will be archived later.
                continue

        files_to_upload = {details['file_name'] for details in latest_files_per_store.values()}
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Found {len(files_to_upload)} files to upload out of {len(all_files)} total files."))

        for file_name in all_files:
            file_path = os.path.join(outbox_path, file_name)
            archive_file_path = os.path.join(archive_path, file_name)

            if file_name in files_to_upload:
                # This is the most recent file for a store, so upload and then archive
                self.command.stdout.write(f"--- Processing latest file for store: {file_name} ---")

                # 0. Run sanity checks and clean the file
                self.command.stdout.write(f"--- Running sanity checks on {file_name} ---")
                errors = run_sanity_checks(file_path)
                if errors:
                    self.command.stdout.write(self.command.style.WARNING(f"Found and fixed {len(errors)} issues in {file_name}:"))
                    for error in errors:
                        if "File sanitized" in error:
                            self.command.stdout.write(self.command.style.SUCCESS(f"  - {error}"))
                        else:
                            self.command.stdout.write(self.command.style.ERROR(f"  - {error}"))
                else:
                    continue
                compressed_file_path = file_path + '.gz'

                # 1. Compress the file
                try:
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(compressed_file_path, 'wb') as f_out:
                            f_out.writelines(f_in)
                    self.command.stdout.write(self.command.style.SUCCESS(f"Successfully compressed {file_name}"))
                except Exception as e:
                    self.command.stderr.write(self.command.style.ERROR(f"Failed to compress {file_name}: {e}"))
                    # Archive and continue
                    os.replace(file_path, archive_file_path)
                    self.command.stdout.write(self.command.style.WARNING(f"Archived {file_name} despite compression error."))
                    continue

                # 2. Upload the compressed file
                try:
                    with open(compressed_file_path, 'rb') as f:
                        files = {'file': (os.path.basename(compressed_file_path), f)}
                        response = requests.post(upload_url, headers=headers, files=files, timeout=120)
                    
                    response.raise_for_status()

                    self.command.stdout.write(self.command.style.SUCCESS(f"Successfully uploaded {file_name}"))

                    # 3. Archive the original file
                    os.replace(file_path, archive_file_path)

                except requests.exceptions.RequestException as e:
                    self.command.stderr.write(self.command.style.ERROR(f"Failed to upload {file_name}: {e}"))
                    # If upload fails, still archive the file
                    os.replace(file_path, archive_file_path)
                    self.command.stdout.write(self.command.style.WARNING(f"Archived {file_name} despite upload failure."))
                finally:
                    # 4. Clean up the compressed file
                    if os.path.exists(compressed_file_path):
                        os.remove(compressed_file_path)
            else:
                # Not the latest file for a store, or an error occurred during processing, just archive it
                os.replace(file_path, archive_file_path)
                self.command.stdout.write(self.command.style.SUCCESS(f"Archived outdated or unreadable file: {file_name}"))
