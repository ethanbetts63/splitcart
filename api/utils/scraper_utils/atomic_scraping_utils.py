
import os
import json
import shutil

def append_to_temp_file(product_data, temp_file_path):
    """Appends a product's JSON data to a temporary file."""
    with open(temp_file_path, 'a', encoding='utf-8') as f:
        json.dump(product_data, f)
        f.write('\n')

def finalize_scrape(temp_file_path, inbox_path):
    """Moves the completed temporary file to the product_inbox."""
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path)
    
    shutil.move(temp_file_path, inbox_path)

