import os
import time
import json
from django.conf import settings
from api.utils.database_updating_utils.consolidate_inbox_data import process_product_data
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
        files_to_process = [f for f in os.listdir(inbox_path) if f.endswith('.jsonl')]
        
        if not files_to_process:
            command.stdout.write(command.style.SUCCESS("No more files in the inbox. Main update complete."))
            break
        
        # Process one file at a time
        filename = files_to_process[0]
        file_path = os.path.join(inbox_path, filename)
        
        command.stdout.write(f"--- Processing file: {filename} ---")
        
        consolidated_data = {}
        barcode_to_key_map = {}
        skipped_products_tally = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if process_product_data(data, consolidated_data, barcode_to_key_map, command, filename):
                            skipped_products_tally += 1
            
            if skipped_products_tally > 0:
                command.stdout.write(command.style.WARNING(f"Skipped {skipped_products_tally} products from this file due to missing key data."))

            command.stdout.write(f'Consolidated to {len(consolidated_data)} unique products from this file.')
            
            # Pass a list with the single processed file
            processed_files = [file_path]
            update_database_from_consolidated_data(consolidated_data, processed_files, command)

        except json.JSONDecodeError:
            command.stderr.write(command.style.ERROR(f'Invalid JSON in {filename}. Skipping file.'))
            # Move problematic file to a failed directory? For now, just skip and it will be picked up again.
            time.sleep(5) # Avoid rapid looping on a bad file
            continue
        except Exception as e:
            command.stderr.write(command.style.ERROR(f'An unexpected error occurred processing {filename}: {e}'))
            # Avoid rapid looping on a file that causes other errors
            time.sleep(5) 
            continue

    # --- Post-update cleanup and reconciliation (runs once after all files are processed) ---
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
