import pandas as pd
from companies.models import Store, Company
from products.models import Product, Price
from django.db.models import Count

def group_stores_by_price_correlation(company_name, threshold=99.5):
    """
    Groups stores based on the percentage of common products with identical prices.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company '{company_name}' not found.")
        return [], []

    stores = Store.objects.filter(company=company)
    store_count = stores.count()
    if store_count < 2:
        print("Need at least 2 stores to compare.")
        return [], list(stores)

    # Build a graph where an edge exists if the correlation is above the threshold
    graph = {store.id: [] for store in stores}
    for i in range(store_count):
        for j in range(i + 1, store_count):
            store1 = stores[i]
            store2 = stores[j]

            # Find common products
            products1 = set(Product.objects.filter(prices__store=store1).values_list('id', flat=True))
            products2 = set(Product.objects.filter(prices__store=store2).values_list('id', flat=True))
            common_product_ids = products1.intersection(products2)

            if not common_product_ids:
                correlation = 0.0
            else:
                identical_price_count = 0
                for product_id in common_product_ids:
                    try:
                        price1 = Price.objects.filter(product_id=product_id, store=store1).latest('scraped_at').price
                        price2 = Price.objects.filter(product_id=product_id, store=store2).latest('scraped_at').price
                        if price1 is not None and price1 == price2:
                            identical_price_count += 1
                    except Price.DoesNotExist:
                        continue
                correlation = (identical_price_count / len(common_product_ids)) * 100 if len(common_product_ids) > 0 else 0.0
            
            if correlation >= threshold:
                graph[store1.id].append(store2.id)
                graph[store2.id].append(store1.id)

    # Find connected components (the groups) using DFS
    groups = []
    visited = set()
    for store_id in graph:
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
            groups.append(group)

    # Identify island stores
    grouped_store_ids = {store_id for group in groups for store_id in group if len(group) > 1}
    all_store_ids = {store.id for store in stores}
    island_store_ids = all_store_ids - grouped_store_ids
    
    # Convert store IDs back to store objects
    store_map = {store.id: store for store in stores}
    final_groups = [[store_map[store_id] for store_id in group] for group in groups if len(group) > 1]
    island_stores = [store_map[store_id] for store_id in island_store_ids]

    return final_groups, island_stores
