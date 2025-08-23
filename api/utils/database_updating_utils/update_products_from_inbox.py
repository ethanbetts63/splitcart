import os
import time
from django.conf import settings
from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data
from api.utils.database_updating_utils.update_database_from_consolidated_data import update_database_from_consolidated_data

def update_products_from_inbox(command):
    inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')

    if not os.path.exists(inbox_path):
        command.stdout.write(command.style.WARNING('Product inbox directory not found.'))
        return

    while True:
        jsonl_files = [f for f in os.listdir(inbox_path) if f.endswith('.jsonl')]
        
        if not jsonl_files:
            command.stdout.write(command.style.SUCCESS("No files in the inbox. Waiting 30 seconds..."))
            time.sleep(30) # First wait if no files
            jsonl_files = [f for f in os.listdir(inbox_path) if f.endswith('.jsonl')]
            if not jsonl_files:
                command.stdout.write(command.style.SUCCESS("No new files found after waiting. Exiting."))
                break # Exit if still no files after first wait
        
        # If we reach here, it means there are files to process (either initially or after the first wait)
        consolidated_data, processed_files = consolidate_inbox_data(inbox_path, command)
        update_database_from_consolidated_data(consolidated_data, processed_files, command)
