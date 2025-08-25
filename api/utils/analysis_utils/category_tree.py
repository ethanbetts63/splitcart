from collections import defaultdict
from companies.models import Category, Company

def _build_tree_string_from_map(category, children_map, prefix="", is_last=True, visited=None):
    """Recursively builds the tree string from an in-memory map."""
    if visited is None:
        visited = set()
    
    if category['id'] in visited:
        return f"{prefix}└── [CYCLE DETECTED: {category['name']}]\n"
    
    visited.add(category['id'])

    connector = "└── " if is_last else "├── "
    tree_string = f"{prefix}{connector}{category['name']}\n"
    
    children = sorted(children_map.get(category['id'], []), key=lambda x: x['name'])
    child_count = len(children)

    for i, child in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        tree_string += _build_tree_string_from_map(
            child, children_map, prefix=new_prefix, is_last=(i == child_count - 1), visited=visited.copy()
        )
        
    return tree_string

def generate_category_tree(company_name: str):
    """
    Generates a string representation of the category tree for a given company
    by fetching all data first to prevent recursion issues with the ORM.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        return f"Error: Company '{company_name}' not found."

    # 1. Fetch all categories and their parent relationships for the company
    all_categories_data = Category.objects.filter(company=company).values('id', 'name', 'parents__id')

    if not all_categories_data:
        return f"No categories found for {company.name}."

    # 2. Build in-memory maps
    categories_by_id = {cat['id']: {'id': cat['id'], 'name': cat['name']} for cat in all_categories_data}
    
    children_map = defaultdict(list)
    root_ids = set(categories_by_id.keys())

    for cat_data in all_categories_data:
        parent_id = cat_data.get('parents__id')
        if parent_id:
            # Ensure the child is unique in the list for a given parent
            if categories_by_id[cat_data['id']] not in children_map[parent_id]:
                children_map[parent_id].append(categories_by_id[cat_data['id']])
            if cat_data['id'] in root_ids:
                root_ids.remove(cat_data['id']) # It has a parent, so it's not a root

    # 3. Get the root category objects
    root_nodes = sorted([categories_by_id[rid] for rid in root_ids], key=lambda x: x['name'])

    if not root_nodes:
        return f"Error: No root categories found for {company.name}. There might be a cycle in the data."

    # 4. Build the tree string
    tree_output = f"Category Tree for {company.name}:\n"
    category_count = len(root_nodes)
    for i, category in enumerate(root_nodes):
        tree_output += _build_tree_string_from_map(category, children_map, prefix="", is_last=(i == category_count - 1))

    return tree_output
