from django.utils.text import slugify
from companies.models import Category, Company

def get_or_create_category(name: str, company: Company, store_category_id: str = None) -> tuple[Category, bool]:
    """
    Finds or creates a single category instance based on its slug.
    The slug is the primary identifier for a category within a company.
    """
    slug = slugify(name)
    
    # Get or create the category based on its unique identity (slug, company).
    # 'name' is in defaults, so if the category already exists, its name is not changed.
    # This respects the "first name wins" for a given slug.
    category, created = Category.objects.get_or_create(
        slug=slug,
        company=company.id,
        defaults={'name': name, 'store_category_id': store_category_id}
    )
    return category, created
