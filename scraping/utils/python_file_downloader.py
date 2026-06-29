import os
import requests
from django.conf import settings

def fetch_python_file(file_name: str, destination_path: str, command=None, base_url=None):
    """
    Fetches a file from the server API and saves it to the specified path.

    Args:
        file_name (str): The name of the file to fetch (e.g., 'product_translations').
        destination_path (str): The full local path to save the .py file.
        command: Optional Django command object for logging.
        base_url (str, optional): The base URL of the server. Defaults to settings.API_SERVER_URL.
    """
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    server_url = base_url or settings.API_SERVER_URL
    api_key = settings.INTERNAL_API_KEY
    if not server_url or not api_key:
        if command:
            command.stdout.write(command.style.ERROR(f"API_SERVER_URL or INTERNAL_API_KEY not configured."))
        return

    url = f"{server_url.rstrip('/')}/api/files/{file_name}/"
    headers = {
        'X-Internal-API-Key': api_key,
    }

    try:
        if command:
            command.stdout.write(f"Fetching '{os.path.basename(destination_path)}' file...")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save the new file content
        with open(destination_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        if command:
            command.stdout.write(command.style.SUCCESS(f"- Successfully downloaded and updated '{os.path.basename(destination_path)}'."))

    except requests.exceptions.RequestException as e:
        if command:
            command.stdout.write(command.style.ERROR(f"Failed to fetch '{os.path.basename(destination_path)}' file: {e}"))
