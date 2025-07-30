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
                '2025-07-30T16:51:12.123456': {  // A unique scrape timestamp
                    'fruit-vegetables': ['path/to/page1.json', 'path/to/page2.json'],
                    'meat-seafood': ['path/to/page1.json']
                }
            },
            'woolworths': { ... }
        }
        Returns an empty dict if the directory doesn't exist or is empty.
    """
    if not os.path.isdir(raw_data_path):
        print(f"Warning: Raw data directory not found at '{raw_data_path}'")
        return {}

    # The structure will be: store -> scrape_timestamp -> category -> list of file paths
    scrape_plan = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

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

                store = metadata.get('store')
                category = metadata.get('category')
                scrape_timestamp = metadata.get('scraped_at')

                if store and category and scrape_timestamp:
                    # Use the first 19 characters (YYYY-MM-DDTHH:MM:SS) of the timestamp
                    # to group all pages from a single scraper run together.
                    scrape_run_id = scrape_timestamp[:19]
                    scrape_plan[store][scrape_run_id][category].append(file_path)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read or parse {filename}. Error: {e}")

    # Sort the page files for each category to ensure they are processed in order
    for store in scrape_plan:
        for timestamp in scrape_plan[store]:
            for category in scrape_plan[store][timestamp]:
                scrape_plan[store][timestamp][category].sort(
                    key=lambda f: json.load(open(f))['metadata']['page_number']
                )

    return json.loads(json.dumps(scrape_plan)) # Convert defaultdicts to regular dicts
