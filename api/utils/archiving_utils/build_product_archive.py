import multiprocessing
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset
from api.utils.archiving_utils.archive_single_store import archive_single_store

def build_product_archive(command, company_slug_arg=None, store_id_arg=None):
    """
    Builds store-specific JSON files.
    """
    command.stdout.write(command.style.SUCCESS('Starting to build store JSON files...'))

    stores_queryset = get_stores_queryset(company_slug_arg, store_id_arg)
    store_ids = list(stores_queryset.values_list('store_id', flat=True))

    total_stores = len(store_ids)
    if total_stores == 0:
        command.stdout.write(command.style.WARNING('No stores found for the given criteria.'))
        return

    command.stdout.write(f'Found {total_stores} store(s) to process...\n')

    # --- SEQUENTIAL EXECUTION FOR TESTING ---
    for i, store_id in enumerate(store_ids, 1):
        result = archive_single_store(store_id)
        status = result.get('status')
        store_name = result.get('store_name', result.get('store_id', 'Unknown'))
        
        progress = f'({i}/{total_stores})'

        if status == 'success':
            products_found = result.get('products_found', 0)
            command.stdout.write(command.style.SUCCESS(f"{progress} Successfully processed {store_name} ({products_found} products): {result['path']}"))
        elif status == 'skipped':
            command.stdout.write(command.style.WARNING(f"{progress} Skipped {store_name}: {result['reason']}"))
        elif status == 'error':
            command.stdout.write(command.style.ERROR(f"{progress} Error processing store {store_name}: {result['error']}"))

    command.stdout.write(command.style.SUCCESS('\nFinished building all store JSON files.'))
