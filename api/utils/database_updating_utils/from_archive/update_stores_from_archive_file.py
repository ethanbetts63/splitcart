
import json
from api.utils.database_updating_utils.get_or_create_company import get_or_create_company
from api.utils.database_updating_utils.get_or_create_division import get_or_create_division
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

def update_stores_from_archive_file(file_path: str) -> (str, int):
    """
    Processes a single company archive JSON file and updates the database with store information.
    This function can handle two structures: one with divisions and one without.

    Args:
        file_path: The absolute path to the JSON file.

    Returns:
        A tuple containing the company name and the total number of stores processed.
        Returns (None, 0) if the file cannot be processed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None, 0

    metadata = data.get('metadata', {})
    company_name = metadata.get('company_name')
    if not company_name:
        return None, 0

    company_obj, _ = get_or_create_company(company_name)
    total_stores_processed = 0

    # Case 1: Company has divisions
    if 'stores_by_division' in data:
        stores_by_division = data.get('stores_by_division', {})
        for division_slug, division_data in stores_by_division.items():
            division_name = division_data.get('division_name')
            if not division_name:
                continue
            
            division_obj, _ = get_or_create_division(company_obj, division_name)
            stores_by_state = division_data.get('stores_by_state', {})

            for state_slug, state_data in stores_by_state.items():
                stores = state_data.get('stores', [])
                for store_data in stores:
                    store_id = store_data.get('store_id')
                    if not store_id:
                        continue
                    
                    get_or_create_store(
                        company_obj=company_obj,
                        division_obj=division_obj,
                        store_id=store_id,
                        store_data=store_data
                    )
                    total_stores_processed += 1

    # Case 2: Company has no divisions
    elif 'stores_by_state' in data:
        stores_by_state = data.get('stores_by_state', {})
        for state_slug, state_data in stores_by_state.items():
            stores = state_data.get('stores', [])
            for store_data in stores:
                store_id = store_data.get('store_id')
                if not store_id:
                    continue
                
                get_or_create_store(
                    company_obj=company_obj,
                    division_obj=None,  # No division
                    store_id=store_id,
                    store_data=store_data
                )
                total_stores_processed += 1
            
    return company_name, total_stores_processed
