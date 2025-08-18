from django.utils.text import slugify
from datetime import datetime
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset
from api.utils.archiving_utils.build_product_list import build_product_list
from api.utils.archiving_utils.save_json_file import save_json_file
from api.utils.archiving_utils.print_product_progress import print_product_progress

def build_product_archive(command, company_slug_arg=None, store_id_arg=None):
    """
    Builds store-specific JSON files with product and price data.
    """
    command.stdout.write(command.style.SUCCESS('Starting to build store JSON files...'))

    stores_to_process = get_stores_queryset(company_slug_arg, store_id_arg)

    total_stores = stores_to_process.count()
    if total_stores == 0:
        command.stdout.write(command.style.WARNING('No stores found for the given criteria.'))
        return

    command.stdout.write(f'Found {total_stores} store(s) to process...')

    for i, store in enumerate(stores_to_process.iterator(), 1):
        command.stdout.write(f'\n({i}/{total_stores}) Processing store: {store.store_name} ({store.store_id})...')

        product_list = []
        products_processed_count = 0
        for product_data in build_product_list(store):
            products_processed_count += 1
            print_product_progress(products_processed_count)
            product_list.append(product_data)

        if products_processed_count == 0:
            command.stdout.write(command.style.WARNING(f'  Skipping store: No products found.'))
            continue
        
        command.stdout.write("") 

        store_data = {
            'metadata': {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'company_name': store.company.name,
                'address_line_1': store.address_line_1,
                'suburb': store.suburb,
                'state': store.state,
                'postcode': store.postcode,
                'data_generation_date': datetime.now().isoformat(),
            },
            'products': product_list
        }

        company_slug = slugify(store.company.name)
        saved_path = save_json_file(company_slug, store.store_id, store_data)
        command.stdout.write(command.style.SUCCESS(f'  Successfully created file: {saved_path}'))

    command.stdout.write(command.style.SUCCESS('\nFinished building all store JSON files.'))
