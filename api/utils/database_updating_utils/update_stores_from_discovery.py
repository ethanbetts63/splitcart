import os
import time
from django.conf import settings
from api.utils.database_updating_utils.tally_counter import TallyCounter
from api.utils.database_updating_utils.process_store_file import process_store_file

def update_stores_from_discovery(command):
    discovered_stores_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'discovered_stores')
    tally = TallyCounter()

    if not os.path.exists(discovered_stores_dir):
        command.stdout.write(command.style.WARNING(f"'{discovered_stores_dir}' not found. Nothing to process."))
        return

    while True:
        store_files = [f for f in os.listdir(discovered_stores_dir) if f.endswith('.json')]

        if store_files:
            command.stdout.write(command.style.SQL_FIELD(f"Found {len(store_files)} file(s) to process..."))
            for file_name in store_files:
                process_store_file(file_name, discovered_stores_dir, command, tally)
            continue  # Check for more files immediately

        # If no files are found, wait and check again
        command.stdout.write(command.style.SQL_FIELD("No new store files found. Waiting 1000 seconds..."))
        time.sleep(1000)

        store_files_after_wait = [f for f in os.listdir(discovered_stores_dir) if f.endswith('.json')]
        if not store_files_after_wait:
            command.stdout.write(command.style.SUCCESS("No new files found after waiting. Exiting."))
            break  # Exit the loop
