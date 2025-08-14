def build_tree(categories):
    """
    Builds a hierarchical tree from a flat list of category objects.
    """
    # Create a map of category IDs to dictionary representations
    category_map = {cat.id: {'name': cat.name, 'slug': cat.slug, 'children': []} for cat in categories}
    root_nodes = []

    for cat in categories:
        has_parent_in_set = False
        # The category model uses a ManyToManyField for parents
        for parent in cat.parents.all():
            if parent.id in category_map:
                # Append this category to its parent's list of children
                category_map[parent.id]['children'].append(category_map[cat.id])
                has_parent_in_set = True
        
        # If a category has no parents within this specific set, it is a root node.
        if not has_parent_in_set:
            root_nodes.append(category_map[cat.id])

    return root_nodes

def construct_category_hierarchy(store):
    """
    Constructs a hierarchical representation of categories for a given store.

    Args:
        store (Store): A Store object with product_set__category__parent prefetched.

    Returns:
        list: A list of dictionaries, where each dictionary represents a root category
              and contains its children in a nested structure.
    """
    store_categories = set()
    if not hasattr(store, 'product_set'):
        return []

    # Gather all unique categories and their parents from the store's products
    for product in store.product_set.all():
        if product.category:
            category = product.category
            # Add the category and all its ancestors to the set
            while category:
                if category in store_categories:
                    break # Avoid redundant traversals
                store_categories.add(category)
                # Move to the first parent (in many-to-many, there could be several)
                category = category.parents.first()

    if not store_categories:
        return []

    # Build the tree structure from the flat list of categories
    return build_tree(list(store_categories))
