from companies.models import Category, Company

def get_or_create_category(name: str, company: Company, parent: Category = None, store_category_id: str = None) -> tuple[Category, bool]:
    """
    Finds or creates a single category instance.
    """
    category, created = Category.objects.get_or_create(
        name__iexact=name,
        company=company,
        parent=parent,
        defaults={'name': name, 'store_category_id': store_category_id}
    )
    return category, created
