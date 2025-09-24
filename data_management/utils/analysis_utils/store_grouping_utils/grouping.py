def find_store_groups(store_map, graph):
    """
    Finds connected components in the graph to group stores.
    Also identifies island stores (stores not in any group).
    """
    groups = []
    visited = set()
    store_ids = list(store_map.keys())

    for store_id in store_ids:
        if store_id not in visited:
            group = []
            stack = [store_id]
            visited.add(store_id)
            while stack:
                node = stack.pop()
                group.append(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            if len(group) > 1:
                groups.append(group)

    # Identify island stores
    grouped_store_ids = {store_id for group in groups for store_id in group}
    all_store_ids = set(store_ids)
    island_store_ids = all_store_ids - grouped_store_ids

    # Convert store IDs back to store objects
    final_groups = [[store_map[store_id] for store_id in group] for group in groups]
    island_stores = [store_map[store_id] for store_id in island_store_ids]

    return final_groups, island_stores
