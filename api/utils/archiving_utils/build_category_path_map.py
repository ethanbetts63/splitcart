from companies.models import Category

def build_category_path_map(category_ids):
    """
    Builds a map of category IDs to their full hierarchical paths efficiently.

    Args:
        category_ids (list): A list of category IDs to build paths for.

    Returns:
        dict: A dictionary mapping each category ID to a list of strings 
              representing its path (e.g., {123: ['Parent', 'Child', 'Grandchild']}).
    """
    if not category_ids:
        return {}

    path_map = {}
    # Fetch all relevant categories and their direct parents in one go.
    # We use values() to get just the data we need, which is faster.
    categories_data = Category.objects.filter(id__in=category_ids).values('id', 'name', 'parents__id', 'parents__name')

    # A dictionary to hold parent-child relationships for all categories in the system.
    # This is a trade-off: it might be a large query, but it's only run once.
    # A more memory-efficient way might involve iterative queries, but this is often faster.
    all_parents_map = {c['id']: {'name': c['name'], 'parent_id': c['parents__id']} for c in Category.objects.values('id', 'name', 'parents__id')}

    for cat_id in category_ids:
        path = []
        current_id = cat_id
        depth = 0
        max_depth = 20 # Safeguard against infinite loops

        while current_id and depth < max_depth:
            category_info = all_parents_map.get(current_id)
            if not category_info:
                break
            
            path.insert(0, category_info['name'])
            current_id = category_info['parent_id']
            depth += 1
        
        path_map[cat_id] = path

    return path_map
