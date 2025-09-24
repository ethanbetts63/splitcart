from data_management.utils.analysis_utils.store_grouping_utils.data_fetching import get_store_product_prices
from data_management.utils.analysis_utils.store_grouping_utils.graph_construction import build_correlation_graph
from data_management.utils.analysis_utils.store_grouping_utils.grouping import find_store_groups

def group_stores_by_price_correlation(company_name, threshold=99.5):
    """
    Groups stores based on the percentage of common products with identical prices.
    """
    # Step 1: Fetch all necessary data from the database
    store_map, store_price_data = get_store_product_prices(company_name)
    if not store_map or not store_price_data:
        return [], []

    # Step 2: Build the correlation graph in memory
    graph = build_correlation_graph(store_map, store_price_data, threshold)

    # Step 3: Find connected components to form groups
    final_groups, island_stores = find_store_groups(store_map, graph)

    return final_groups, island_stores