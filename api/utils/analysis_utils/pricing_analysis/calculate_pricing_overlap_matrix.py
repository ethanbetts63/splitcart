
import pandas as pd

def calculate_pricing_overlap_matrix(store_product_prices):
    """
    Calculates the pricing overlap matrix.

    Args:
        store_product_prices (dict): A dictionary mapping store names to a dictionary of product IDs to prices.

    Returns:
        tuple: A tuple containing four DataFrames:
            - overlap_matrix: Raw count of products with identical prices.
            - percent_of_row_matrix: Percentage of products in the row store that have identical prices in the column store.
            - percent_of_col_matrix: Percentage of products in the column store that have identical prices in the row store.
            - average_percentage_matrix: Average of the two percentage matrices.
    """
    stores = list(store_product_prices.keys())
    num_stores = len(stores)
    
    # Initialize matrices
    overlap_matrix = pd.DataFrame(0, index=stores, columns=stores)
    percent_of_row_matrix = pd.DataFrame(0.0, index=stores, columns=stores)
    percent_of_col_matrix = pd.DataFrame(0.0, index=stores, columns=stores)

    for i in range(num_stores):
        for j in range(num_stores):
            store1_name = stores[i]
            store2_name = stores[j]
            
            store1_products = store_product_prices[store1_name]
            store2_products = store_product_prices[store2_name]
            
            if i == j:
                overlap_matrix.iloc[i, j] = len(store1_products)
                percent_of_row_matrix.iloc[i, j] = 100.0
                percent_of_col_matrix.iloc[i, j] = 100.0
            else:
                overlapping_products = set(store1_products.keys()) & set(store2_products.keys())
                identically_priced_count = 0
                for product_id in overlapping_products:
                    if store1_products[product_id] == store2_products[product_id]:
                        identically_priced_count += 1
                
                overlap_matrix.iloc[i, j] = identically_priced_count
                
                if len(store1_products) > 0:
                    percent_of_row_matrix.iloc[i, j] = (identically_priced_count / len(overlapping_products)) * 100 if len(overlapping_products) > 0 else 0
                
                if len(store2_products) > 0:
                    percent_of_col_matrix.iloc[i, j] = (identically_priced_count / len(overlapping_products)) * 100 if len(overlapping_products) > 0 else 0

    average_percentage_matrix = (percent_of_row_matrix + percent_of_col_matrix) / 2

    return overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix
