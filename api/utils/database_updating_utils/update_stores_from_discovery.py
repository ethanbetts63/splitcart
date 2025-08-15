import json
import os
from django.conf import settings
from api.utils.database_updating_utils.get_or_create_company import get_or_create_company
from api.utils.database_updating_utils.get_or_create_division import get_or_create_division
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store
from api.utils.database_updating_utils.tally_counter import TallyCounter

def process_store_file(file_name, directory, command, tally):
    file_path = os.path.join(directory, file_name)
    command.stdout.write(command.style.SUCCESS(f"Processing file: {file_name}"))
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            store_data_full = json.load(f)

        metadata = store_data_full.get('metadata', {})
        store_data = store_data_full.get('store_data', {})
        company_name = metadata.get('company')
        
        division_name, external_id, store_finder_id = None, None, None
        if company_name == "Coles":
            brand_data = store_data.get('brand', {})
            division_name = brand_data.get('name')
            external_id = brand_data.get('id')
            store_finder_id = brand_data.get('storeFinderId')
        elif company_name == "Woolworths":
            division_name = store_data.get('Division')

        store_id = store_data.get('store_id')

        if not company_name or not store_id:
            command.stdout.write(command.style.ERROR(f"Skipping {file_name}: Missing company name or store ID."))
            os.remove(file_path)
            return

        company_obj, company_created = get_or_create_company(company_name)
        division_obj = None
        if division_name:
            division_obj, division_created = get_or_create_division(
                company_obj=company_obj, division_name=division_name,
                external_id=external_id, store_finder_id=store_finder_id
            )
        store_obj, store_created = get_or_create_store(
            company_obj=company_obj, division_obj=division_obj,
            store_id=store_id,
            store_data=store_data
        )
        
        tally.increment(store_created, company_name)
        os.remove(file_path)
        tally.display(command)

    except json.JSONDecodeError:
        command.stdout.write(command.style.ERROR(f"Error decoding JSON from {file_name}. Removing."))
        os.remove(file_path)
    except Exception as e:
        command.stdout.write(command.style.ERROR(f"An unexpected error occurred while processing {file_name}: {e}"))
        os.remove(file_path)

def update_stores_from_discovery(command):
    discovered_stores_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'discovered_stores')
    tally = TallyCounter()

    if not os.path.exists(discovered_stores_dir):
        command.stdout.write(command.style.WARNING(f"'{discovered_stores_dir}' not found. Nothing to process."))
        return

    store_files = [f for f in os.listdir(discovered_stores_dir) if f.endswith('.json')]

    if store_files:
        command.stdout.write(command.style.SUCCESS(f"Found {len(store_files)} file(s) to process..."))
        for file_name in store_files:
            process_store_file(file_name, discovered_stores_dir, command, tally)
    else:
        command.stdout.write(command.style.SUCCESS("No new store files found."))
