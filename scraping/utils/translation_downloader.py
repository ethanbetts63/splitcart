import os
import requests
import gzip
import json
from django.conf import settings

# Define the local directory to cache the translation tables
CACHE_DIR = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'translations')

def fetch_translation_table(table_name: str, command=None):
    """
    Fetches a translation table from the server API, using a local cache
    and ETag to avoid unnecessary downloads.

    Args:
        table_name (str): The name of the table to fetch (e.g., 'products', 'brands').
        command: Optional Django command object for logging.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    server_url = settings.API_SERVER_URL
    api_key = settings.API_SECRET_KEY
    if not server_url or not api_key:
        if command:
            command.stdout.write(command.style.ERROR(f"API_SERVER_URL or API_SECRET_KEY not configured."))
        return

    url = f"{server_url.rstrip('/')}/api/translations/{table_name}/"
    headers = {
        'Authorization': f'Api-Key {api_key}',
        'Accept-Encoding': 'gzip'
    }

    cache_path = os.path.join(CACHE_DIR, f'{table_name}.json')
    etag_path = os.path.join(CACHE_DIR, f'{table_name}.json.etag')

    # Check for a cached ETag and add it to the request headers
    if os.path.exists(etag_path):
        with open(etag_path, 'r') as f:
            etag = f.read().strip()
            headers['If-None-Match'] = etag

    try:
        if command:
            command.stdout.write(f"Checking for updated '{table_name}' translation table...")
        
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 304:
            if command:
                command.stdout.write(command.style.SUCCESS(f"- '{table_name}' table is up to date."))
            return

        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Save the new ETag
        new_etag = response.headers.get('ETag')
        if new_etag:
            with open(etag_path, 'w') as f:
                f.write(new_etag)

        # Decompress and save the new data
        data = json.loads(gzip.decompress(response.content))
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=4)

        if command:
            command.stdout.write(command.style.SUCCESS(f"- Successfully downloaded and updated '{table_name}' translation table."))

    except requests.exceptions.RequestException as e:
        if command:
            command.stdout.write(command.style.ERROR(f"Failed to fetch '{table_name}' table: {e}"))
