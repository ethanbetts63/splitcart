import os
import json
from collections import defaultdict

def file_finder(raw_data_path: str) -> dict:
    """
    Scans the raw_data directory, reads metadata from each JSON file,
    and groups them into a structured dictionary representing individual scrapes.

    Args:
        raw_data_path: The absolute path to the raw_data directory.

    Returns:
        A nested dictionary structured as:
        {
            'coles': {
                'national': {
                    '2025-08-03': {
                        'fruit-vegetables': ['path/to/page1.json'],
                    }
                }
            },
            'aldi': { ... }
        }
    """
    if not os.path.isdir(raw_data_path):
        print(f"Warning: Raw data directory not found at '{raw_data_path}'")
        return {}

    # The structure is now: company -> state -> store -> scrape_date -> category -> file_paths
    scrape_plan = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))))

    for filename in os.listdir(raw_data_path):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(raw_data_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                metadata = data.get('metadata')
                if not metadata:
                    print(f"Warning: Skipping file with missing metadata: {filename}")
                    continue

                company = metadata.get('company')
                state = metadata.get('state')
                store_name = metadata.get('store_name')
                store_id = metadata.get('store_id')
                category = metadata.get('category')
                scrape_timestamp = metadata.get('scraped_at')

                if all([company, state, store_name, store_id, category, scrape_timestamp]):
                    scrape_date = scrape_timestamp[:10]
                    store_key = store_id
                    scrape_plan[company][state][store_key][scrape_date][category].append(file_path)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read or parse {filename}. Error: {e}")

    # Sort the page files for each category to ensure they are processed in order
    for company in scrape_plan:
        for state in scrape_plan[company]:
            for store in scrape_plan[company][state]:
                for scrape_date in scrape_plan[company][state][store]:
                    for category in scrape_plan[company][state][store][scrape_date]:
                        def sort_key(file_path):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    return json.load(f)['metadata']['page_number']
                            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                                return float('inf')
                        
                        scrape_plan[company][state][store][scrape_date][category].sort(key=sort_key)

    return json.loads(json.dumps(scrape_plan)) # Convert defaultdicts to regular dicts