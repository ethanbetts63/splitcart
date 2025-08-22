import os
import time
from django.conf import settings
from .consolidate_inbox_data import consolidate_inbox_data
from .update_database_from_consolidated_data import update_database_from_consolidated_data

def update_products_from_inbox(command):
    inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')

    if not os.path.exists(inbox_path):
        command.stdout.write(command.style.WARNING('Product inbox directory not found.'))
        return

    while True:
        json_files = [f for f in os.listdir(inbox_path) if f.endswith('.json')]
        if not json_files:
            command.stdout.write(command.style.SUCCESS("No files in the inbox. Waiting 60 seconds..."))
            time.sleep(60)
            json_files = [f for f in os.listdir(inbox_path) if f.endswith('.json')]
            if not json_files:
                command.stdout.write(command.style.SUCCESS("No new files found after waiting. Exiting."))
                break
        
        consolidated_data, processed_files = consolidate_inbox_data(inbox_path, command)
        update_database_from_consolidated_data(consolidated_data, processed_files, command)