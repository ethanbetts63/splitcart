import re

def create_store_slug_woolworths(store_name: str) -> str:
    """Creates a clean, lowercase, URL-friendly slug from a store name."""
    slug = store_name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug).strip('-')
    return slug
