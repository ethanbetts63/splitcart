import pandas as pd
from itertools import combinations

def calculate_overlap_matrices(entity_products):
    """
    Calculates overlap matrices from product sets.

    Args:
        entity_products (dict): A dictionary mapping entity names to a set of product IDs.

    Returns:
        tuple: A tuple containing four pandas DataFrames: 
               overlap_matrix, percent_of_row_matrix, 
               percent_of_col_matrix, average_percentage_matrix.
    """
    entity_names = list(entity_products.keys())
    
    print("    Calculating co-occurrence matrix...")
    # Create empty DataFrames for raw counts and percentages
    overlap_matrix = pd.DataFrame(0, index=entity_names, columns=entity_names)
    percent_of_row_matrix = pd.DataFrame(0.0, index=entity_names, columns=entity_names)
    percent_of_col_matrix = pd.DataFrame(0.0, index=entity_names, columns=entity_names)
    average_percentage_matrix = pd.DataFrame(0.0, index=entity_names, columns=entity_names)

    # Calculate the overlap (intersection) for each pair of entities
    for entity1, entity2 in combinations(entity_names, 2):
        intersection_size = len(entity_products[entity1].intersection(entity_products[entity2]))
        
        total_products_e1 = len(entity_products[entity1])
        total_products_e2 = len(entity_products[entity2])

        # Raw counts
        overlap_matrix.loc[entity1, entity2] = intersection_size
        overlap_matrix.loc[entity2, entity1] = intersection_size

        # Percentages
        percent_e1_in_e2 = (intersection_size / total_products_e1) * 100 if total_products_e1 > 0 else 0
        percent_e2_in_e1 = (intersection_size / total_products_e2) * 100 if total_products_e2 > 0 else 0

        percent_of_row_matrix.loc[entity1, entity2] = percent_e1_in_e2
        percent_of_col_matrix.loc[entity1, entity2] = percent_e2_in_e1

        percent_of_row_matrix.loc[entity2, entity1] = percent_e2_in_e1 # Note the swap for symmetry
        percent_of_col_matrix.loc[entity2, entity1] = percent_e1_in_e2 # Note the swap for symmetry

        # Average percentage
        average_percentage_matrix.loc[entity1, entity2] = (percent_e1_in_e2 + percent_e2_in_e1) / 2
        average_percentage_matrix.loc[entity2, entity1] = (percent_e1_in_e2 + percent_e2_in_e1) / 2

    # Fill the diagonal for raw counts (total unique products for each entity)
    for entity_name in entity_names:
        total_unique = len(entity_products[entity_name])
        overlap_matrix.loc[entity_name, entity_name] = total_unique
        percent_of_row_matrix.loc[entity_name, entity_name] = 100.0
        percent_of_col_matrix.loc[entity_name, entity_name] = 100.0
        average_percentage_matrix.loc[entity_name, entity_name] = 100.0
        
    return overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix
