from collections import defaultdict
from companies.models import Category, Company

def _build_tree_string_from_map(category, children_map, prefix="", is_last=True, visited=None, command=None, counter=None):
    """Recursively builds the tree string, now with correct visited tracking."""
    # The 'visited' set is now passed by reference and shared across all calls for a single root tree.
    if visited is None:
        visited = set()
    
    # If we have seen this node before in this traversal, it's part of a cycle with its parent.
    # However, the more general case is that it's a node we have already processed completely.
    # The check below handles both.
    if category['id'] in visited:
        # We simply don't render it again. If it's a true cycle, the path will just end here.
        return f"{prefix}{connector}[... {category['name']} already rendered ...]\n"

    visited.add(category['id'])
    counter[0] += 1

    if command and counter[0] % 100 == 0:
        command.stdout.write(".", ending="")
        command.stdout.flush()

    connector = "└── " if is_last else "├── "
    tree_string = f"{prefix}{connector}{category['name']}\n"
    
    children = sorted(children_map.get(category['id'], []), key=lambda x: x['name'])
    child_count = len(children)

    for i, child in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        # Pass the SAME visited set down, not a copy.
        tree_string += _build_tree_string_from_map(
            child, children_map, 
            prefix=new_prefix, 
            is_last=(i == child_count - 1), 
            visited=visited,
            command=command,
            counter=counter
        )
        
    return tree_string

def generate_category_tree(company_name: str, command=None):
    """
    Generates a string representation of the category tree for a given company.
    """
    def log(message, style=None):
        if command:
            if style:
                command.stdout.write(style(message))
            else:
                command.stdout.write(message)

    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        return f"Error: Company '{company_name}' not found."

    log("  - Fetching all category data from database...")
    all_categories_data = Category.objects.filter(company=company).values('id', 'name', 'parents__id')

    if not all_categories_data:
        return f"No categories found for {company.name}."
    
    log(f"  - Found {len(all_categories_data)} total category entries.")
    log("  - Building in-memory hierarchy...")

    categories_by_id = {cat['id']: {'id': cat['id'], 'name': cat['name']} for cat in all_categories_data}
    
    children_map = defaultdict(list)
    root_ids = set(categories_by_id.keys())

    for cat_data in all_categories_data:
        parent_id = cat_data.get('parents__id')
        if parent_id and parent_id in categories_by_id:
            if categories_by_id[cat_data['id']] not in children_map[parent_id]:
                children_map[parent_id].append(categories_by_id[cat_data['id']])
            if cat_data['id'] in root_ids:
                root_ids.remove(cat_data['id'])

    root_nodes = sorted([categories_by_id[rid] for rid in root_ids], key=lambda x: x['name'])

    if not root_nodes:
        return f"Error: No root categories found for {company.name}. There might be a cycle in the data."

    log(f"  - Found {len(root_nodes)} root categories. Rendering tree...", style=command.style.SUCCESS if command else None)

    tree_output = f"Category Tree for {company.name}:\n"
    category_count = len(root_nodes)
    # This set will be shared across all branches of all root nodes.
    globally_visited_nodes = set()
    for i, category in enumerate(root_nodes):
        tree_output += _build_tree_string_from_map(
            category, children_map, 
            prefix="", 
            is_last=(i == category_count - 1),
            visited=globally_visited_nodes, # Pass the same set to all
            command=command,
            counter=[0]
        )
        if command:
            command.stdout.write("\n")

    return tree_output