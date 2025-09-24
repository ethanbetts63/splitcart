from itertools import combinations

def build_correlation_graph(store_map, store_price_data, threshold):
    """
    Builds a graph where an edge exists if the price correlation between two stores is above the threshold.
    """
    store_ids = list(store_map.keys())
    graph = {store_id: [] for store_id in store_ids}
    total_comparisons = len(store_ids) * (len(store_ids) - 1) // 2
    current_comparison = 0

    for store1_id, store2_id in combinations(store_ids, 2):
        current_comparison += 1
        print(f"Comparing stores ({current_comparison}/{total_comparisons}): {store_map[store1_id].store_name} and {store_map[store2_id].store_name}")

        products1 = store_price_data[store1_id]
        products2 = store_price_data[store2_id]

        common_product_ids = set(products1.keys()).intersection(set(products2.keys()))

        if not common_product_ids:
            correlation = 0.0
        else:
            identical_price_count = 0
            for product_id in common_product_ids:
                if products1[product_id] == products2[product_id]:
                    identical_price_count += 1
            correlation = (identical_price_count / len(common_product_ids)) * 100

        if correlation >= threshold:
            graph[store1_id].append(store2_id)
            graph[store2_id].append(store1_id)

    return graph
