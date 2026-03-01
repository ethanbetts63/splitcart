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
        total_files = len(all_files)

        if not total_files:
            self.command.stdout.write("No files to process.")
            return

        # --- Stage 1: Scan files ---
        self.command.stdout.write("Scanning files...")
        latest_files_per_store = {}
        files_with_scan_error = set()
        files_skipped_during_scan = set()

        for file_name in all_files:
            file_path = os.path.join(outbox_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if not first_line:
                        files_skipped_during_scan.add(file_name)
                        continue
                    data = json.loads(first_line)
                
                store_id = data.get('metadata', {}).get('store_id')
                scraped_date_str = data.get('metadata', {}).get('scraped_date')

                if not store_id or not scraped_date_str:
                    files_skipped_during_scan.add(file_name)
                    continue
                
                scraped_date = datetime.strptime(scraped_date_str, '%Y-%m-%d').date()

                if store_id not in latest_files_per_store or scraped_date > latest_files_per_store[store_id]['scraped_date']:
                    latest_files_per_store[store_id] = {
                        'file_name': file_name,
                        'scraped_date': scraped_date
                    }
            except (json.JSONDecodeError, IOError):
                files_with_scan_error.add(file_name)
                continue

        files_to_upload = {details['file_name'] for details in latest_files_per_store.values()}
        files_to_upload_count = len(files_to_upload)
        self.command.stdout.write(f"Scan complete. Found {files_to_upload_count} files to upload.")

        # --- Stage 2: Process files ---
        uploaded_count = 0
        archived_count = 0
        error_count = len(files_with_scan_error)
        skipped_count = len(files_skipped_during_scan)

        def print_progress():
            self.command.stdout.write(f"\rUploaded: {uploaded_count}/{files_to_upload_count} | Archived: {archived_count}/{total_files} | Errors: {error_count} | Skipped: {skipped_count}", ending="")

        print_progress()

        for file_name in all_files:
            file_path = os.path.join(outbox_path, file_name)
            archive_file_path = os.path.join(archive_path, file_name)

            if file_name in files_with_scan_error or file_name in files_skipped_during_scan:
                os.replace(file_path, archive_file_path)
                archived_count += 1
                print_progress()
                continue

            if file_name in files_to_upload:
                run_sanity_checks(file_path)
                
                compressed_file_path = file_path + '.gz'
                has_error = False

                try:
                    with open(file_path, 'rb') as f_in, gzip.open(compressed_file_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                except Exception:
                    error_count += 1
                    has_error = True

                if not has_error:
                    try:
                        with open(compressed_file_path, 'rb') as f:
                            files = {'file': (os.path.basename(compressed_file_path), f)}
                            response = requests.post(upload_url, headers=headers, files=files, timeout=120)
                            response.raise_for_status()
                        uploaded_count += 1
                    except requests.exceptions.RequestException:
                        error_count += 1
                
                os.replace(file_path, archive_file_path)
                archived_count += 1
                if os.path.exists(compressed_file_path):
                    os.remove(compressed_file_path)

            else: # Archive outdated files
                os.replace(file_path, archive_file_path)
                archived_count += 1
            
            print_progress()

        self.command.stdout.write("") # Final newline
        self.command.stdout.write("Processing complete.")
