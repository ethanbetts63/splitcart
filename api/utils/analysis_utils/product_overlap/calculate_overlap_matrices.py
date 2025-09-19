import pandas as pd
import numpy as np

def calculate_overlap_matrices(entity_products, stdout=None):
    """
    Calculates overlap matrices from product sets using a vectorized approach.

    Args:
        entity_products (dict): A dictionary mapping entity names to a set of product IDs.
        stdout: Optional command stdout object for writing progress (kept for signature consistency).

    Returns:
        tuple: A tuple containing four pandas DataFrames: 
               overlap_matrix, percent_of_row_matrix, 
               percent_of_col_matrix, average_percentage_matrix.
    """
    if not entity_products:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if stdout:
        stdout.write("    Calculating co-occurrence matrix (vectorized)...")
        stdout.flush()

    # Convert the dict of sets to a long-format list of tuples
    long_format_data = [(entity, product) 
                        for entity, products in entity_products.items() 
                        for product in products]
    
    if not long_format_data:
        # Handle case where there are entities but no products
        entity_names = list(entity_products.keys())
        return pd.DataFrame(0, index=entity_names, columns=entity_names), pd.DataFrame(0.0, index=entity_names, columns=entity_names), pd.DataFrame(0.0, index=entity_names, columns=entity_names), pd.DataFrame(0.0, index=entity_names, columns=entity_names)

    # Create a DataFrame from the long-format data
    df = pd.DataFrame(long_format_data, columns=['entity', 'product'])

    # Create the binary matrix using crosstab
    binary_matrix = pd.crosstab(df['product'], df['entity'])

    # Ensure all original entities are present as columns, even if they have no products
    missing_entities = set(entity_products.keys()) - set(binary_matrix.columns)
    for entity in missing_entities:
        binary_matrix[entity] = 0
    binary_matrix = binary_matrix[list(entity_products.keys())] # Ensure original order

    # Calculate co-occurrence (intersection size) using matrix multiplication
    overlap_matrix = binary_matrix.T.dot(binary_matrix)

    # Get total products per entity (the diagonal of the overlap matrix)
    total_products_per_entity = np.diag(overlap_matrix)

    # To avoid division by zero, replace 0s with a small number (or 1)
    total_products_safe = np.where(total_products_per_entity == 0, 1, total_products_per_entity)

    # Calculate percentage matrices using vectorized operations
    # We divide the overlap matrix by the total products for the row/column entity
    percent_of_row_matrix = overlap_matrix.div(total_products_safe, axis=0)
    percent_of_col_matrix = overlap_matrix.div(total_products_safe, axis=1)

    # Calculate the average percentage matrix
    # This is the mean of (A->B)% and (B->A)%
    average_percentage_matrix = (percent_of_row_matrix + percent_of_row_matrix.T) / 2

    # Set the diagonal of percentage matrices to 1.0 where there are products
    for i, total in enumerate(total_products_per_entity):
        if total > 0:
            percent_of_row_matrix.iloc[i, i] = 1.0
            percent_of_col_matrix.iloc[i, i] = 1.0
            average_percentage_matrix.iloc[i, i] = 1.0

    if stdout:
        stdout.write("\r    Calculating co-occurrence matrix... Done.         \n")
        stdout.flush()

    return overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix
