
import json
import os
import sys

def simplify_store_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"Skipping empty file: {file_path}")
                return
            # Check if the file is already simplified to avoid errors
            if content.strip().startswith('['):
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and data and 'c_internalALDIID' in data[0]:
                        print(f"File already simplified: {file_path}")
                        return
                except json.JSONDecodeError:
                    pass # If it's not a valid JSON list, it needs processing.

            data = json.loads(content)

        simplified_stores = []
        for store in data.get('response', {}).get('entities', []):
            profile = store.get('profile', {})
            address = profile.get('address', {})
            
            simplified_store = {
                'city': address.get('city'),
                'line1': address.get('line1'),
                'postcode': address.get('postalCode'),
                'region': address.get('region'),
                'c_internalALDIID': profile.get('c_internalALDIID'),
                'c_locationName': profile.get('c_locationName')
            }
            simplified_stores.append(simplified_store)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(simplified_stores, f, indent=4)
        print(f"Successfully simplified {file_path}")

    except json.JSONDecodeError:
        print(f"Error decoding JSON in {file_path}. It might be empty, corrupted, or not in the expected format.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}", file=sys.stderr)

def process_directory(root_dir):
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(subdir, file)
                simplify_store_file(file_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python simplify_all_aldi_stores.py <directory_path>")
        sys.exit(1)
    
    target_directory = sys.argv[1]
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at {target_directory}", file=sys.stderr)
        sys.exit(1)
        
    process_directory(target_directory)
