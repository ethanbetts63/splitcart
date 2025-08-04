import re

def create_store_slug_aldi(city_name: str) -> str:
    """Creates a clean, lowercase, URL-friendly slug from a city name."""
    slug = city_name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug).strip('-')
    return slug
