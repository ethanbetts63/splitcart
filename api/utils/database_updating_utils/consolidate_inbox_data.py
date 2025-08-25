import os
import json

def consolidate_inbox_data(inbox_path, command):
    consolidated_data = {}
    processed_files = []
    files_to_process = [f for f in os.listdir(inbox_path) if f.endswith(('.json', '.jsonl'))]
    total_files = len(files_to_process)
    processed_count = 0

    command.stdout.write(f"Found {total_files} files in the inbox to process.")

    for filename in files_to_process:
        processed_count += 1
        command.stdout.write(f'\r  Processing file {processed_count}/{total_files}...', ending='')
        file_path = os.path.join(inbox_path, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.jsonl'):
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            process_product_data(data, consolidated_data)
                else: # .json
                    data = json.load(f)
                    process_product_data(data, consolidated_data)

            processed_files.append(file_path)

        except json.JSONDecodeError:
            command.stderr.write(command.style.ERROR(f'  Invalid JSON in {filename}. Skipping file.'))
            continue
        except Exception as e:
            command.stderr.write(command.style.ERROR(f'  An unexpected error occurred processing {filename}: {e}'))
            continue
    
    command.stdout.write('')
    return consolidated_data, processed_files

def process_product_data(data, consolidated_data):
    product_details = data.get('product', {})
    metadata = data.get('metadata', {})
    
    key = product_details.get('normalized_name_brand_size')
    if not key:
        return

    price_info = {
        'store_id': metadata.get('store_id'),
        'price': product_details.get('price_current'),
        'is_on_special': product_details.get('is_on_special', False),
        'is_available': product_details.get('is_available', True),
        'store_product_id': product_details.get('product_id_store')
    }

    if key in consolidated_data:
        # Key exists, append price history
        consolidated_data[key]['price_history'].append(price_info)
        # Also append category paths if they are new
        category_path = tuple(product_details.get('category_path', []))
        if category_path:
            consolidated_data[key]['category_paths'].add(category_path)
    else:
        # Key is new, create the entry
        category_paths = set()
        raw_path = product_details.get('category_path', [])
        if raw_path:
            category_paths.add(tuple(raw_path))

        consolidated_data[key] = {
            'product_details': product_details,
            'price_history': [price_info],
            'category_paths': category_paths,
            'company_name': metadata.get('company')
        }
