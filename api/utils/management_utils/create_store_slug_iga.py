import re

def create_store_slug_iga(store_name: str) -> str:
    """Creates a clean, lowercase, URL-friendly slug from a store name."""
    # Remove "IGA" and "Fresh" as they are common and redundant
    name = store_name.lower().replace('iga', '').replace('fresh', '')
    # Keep only letters, numbers, and spaces
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # Replace spaces with hyphens and clean up
    slug = re.sub(r'\s+', '-', name).strip('-')
    return slug

