import os
import re
from collections import defaultdict

def group_raw_files_by_scrape(raw_data_path: str) -> dict:
    """
    Scans the raw_data directory, parses the filenames, and groups them
    into a structured dictionary representing individual scrapes.

    Args:
        raw_data_path: The absolute path to the raw_data directory.

    Returns:
        A nested dictionary structured as:
        {
            'coles': {
                '2025-07-30': {
                    'fruit-vegetables': ['path/to/page1.json', 'path/to/page2.json'],
                    'meat-seafood': ['path/to/page1.json']
                }
            },
            'woolworths': { ... }
        }
    """
    if not os.path.isdir(raw_data_path):
        print(f"Warning: Raw data directory not found at '{raw_data_path}'")
        return {}

    # This regex captures the store, category, page number, and date from the filename
    file_pattern = re.compile(
        r'^(?P<store>\w+)_(?P<cat>[\w-]+)_page-(?P<page>\d+)_(?P<date>\d{4}-\d{2}-\d{2})_.*\.json$'
    )

    # Use defaultdict to simplify creating nested dictionaries
    # The structure will be: store -> date -> category -> list of file paths
    scrape_plan = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for filename in os.listdir(raw_data_path):
        match = file_pattern.match(filename)
        if match:
            details = match.groupdict()
            store = details['store']
            date = details['date']
            category = details['cat']
            
            full_path = os.path.join(raw_data_path, filename)
            scrape_plan[store][date][category].append(full_path)

    # Sort the page files for each category to ensure they are processed in order
    for store in scrape_plan:
        for date in scrape_plan[store]:
            for category in scrape_plan[store][date]:
                # Sort based on the page number extracted from the filename
                scrape_plan[store][date][category].sort(
                    key=lambda f: int(file_pattern.match(os.path.basename(f)).group('page'))
                )

    return scrape_plan
