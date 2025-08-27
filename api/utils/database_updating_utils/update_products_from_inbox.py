import os
import time
from django.conf import settings
from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data
from api.utils.database_updating_utils.update_database_from_consolidated_data import update_database_from_consolidated_data
from api.utils.database_updating_utils.create_update_name_variation_hotlist import read_hotlist, clear_hotlist
from api.utils.database_updating_utils.find_duplicate_name_variations import find_duplicates_from_hotlist
from api.utils.database_updating_utils.merge_duplicate_products import merge_products
from api.utils.database_updating_utils.create_update_product_name_translation_table import regenerate_translation_table

def update_products_from_inbox(command):
    inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')

    if not os.path.exists(inbox_path):
        command.stdout.write(command.style.WARNING('Product inbox directory not found.'))
        return

    while True:
        jsonl_files = [f for f in os.listdir(inbox_path) if f.endswith('.jsonl')]
        
        if not jsonl_files:
            command.stdout.write(command.style.SUCCESS("No files in the inbox. Waiting 30 seconds..."))
            time.sleep(30)
            jsonl_files = [f for f in os.listdir(inbox_path) if f.endswith('.jsonl')]
            if not jsonl_files:
                command.stdout.write(command.style.SUCCESS("No new files found after waiting. Main update complete."))
                break
        
        consolidated_data, processed_files = consolidate_inbox_data(inbox_path, command)
        update_database_from_consolidated_data(consolidated_data, processed_files, command)

    # --- Post-update cleanup and reconciliation ---
    command.stdout.write(command.style.SQL_FIELD('--- Running post-update cleanup for name variations ---'))
    
    hotlist = read_hotlist()
    if not hotlist:
        command.stdout.write(command.style.SUCCESS('Hotlist is empty. No duplicates to merge.'))
    else:
        command.stdout.write(f'Found {len(hotlist)} items in the hotlist to process.')
        duplicates_to_merge = find_duplicates_from_hotlist(hotlist)
        
        if not duplicates_to_merge:
            command.stdout.write(command.style.SUCCESS('No duplicate products found in the database based on hotlist.'))
        else:
            command.stdout.write(f'Found {len(duplicates_to_merge)} duplicate products to merge.')
            for item in duplicates_to_merge:
                merge_products(item['canonical'], item['duplicate'])
        
        clear_hotlist()
        command.stdout.write(command.style.SUCCESS('Hotlist has been cleared.'))

    command.stdout.write(command.style.SQL_FIELD('--- Regenerating product name translation table ---'))
    regenerate_translation_table()
    command.stdout.write(command.style.SUCCESS('--- Post-update cleanup complete ---'))