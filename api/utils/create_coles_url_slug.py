import re

def _create_coles_url_slug(name: str, size: str) -> str:
    """Helper function to create a URL-friendly slug from product details."""
    if not name or not size:
        return ""
    combined = f"{name} {size}".lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', combined)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'--+', '-', slug)
    slug = slug.strip('-')
    return slug
