
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from django.conf import settings

def generate_pricing_heatmap_image(overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix, entity_type, company_name=None, state=None):
    """
    Generates and saves a pricing heatmap image from overlap matrices.

    Args:
        overlap_matrix (pd.DataFrame): DataFrame with raw overlap counts of identically priced products.
        percent_of_row_matrix (pd.DataFrame): DataFrame with percentage of row overlap.
        percent_of_col_matrix (pd.DataFrame): DataFrame with percentage of column overlap.
        average_percentage_matrix (pd.DataFrame): DataFrame with average percentage overlap.
        entity_type (str): 'company' or 'store'.
        company_name (str, optional): If entity_type is 'store', the name of the company.
        state (str, optional): If entity_type is 'store', the state to filter stores by.
    """
    print("    Generating pricing heatmap image...")

    # Custom annotation function for heatmap
    def annot_format(val, row_idx, col_idx):
        entity1 = overlap_matrix.index[row_idx]
        entity2 = overlap_matrix.columns[col_idx]
        
        raw_count = overlap_matrix.loc[entity1, entity2]
        percent_row = percent_of_row_matrix.loc[entity1, entity2]
        percent_col = percent_of_col_matrix.loc[entity1, entity2]

        if entity1 == entity2:
            return f"Total Products: {raw_count}\n100%"
        else:
            return f"Identical Prices: {raw_count}\n% of {entity1}: {percent_row:.1f}%\n% of {entity2}: {percent_col:.1f}%"

    # Create a custom annotation array
    annot_array = overlap_matrix.copy().astype(str)
    for r_idx in range(overlap_matrix.shape[0]):
        for c_idx in range(overlap_matrix.shape[1]):
            annot_array.iloc[r_idx, c_idx] = annot_format(None, r_idx, c_idx)

    # Re-plot with custom annotations
    plt.figure(figsize=(16, 14)) # Increased size for more text
    sns.heatmap(average_percentage_matrix, annot=annot_array, fmt='s', cmap='viridis', cbar=True, 
                xticklabels=True, yticklabels=True, 
                annot_kws={"fontsize":8})

    if entity_type == 'company':
        title = 'Pricing Overlap Between Companies (Average Percentage)'
        filename_suffix = 'company-pricing-heatmap'
    else:
        if state:
            title = f'Pricing Overlap Between Stores for {company_name} in {state} (Average Percentage)'
            filename_suffix = f'{company_name.lower()}-{state.lower()}-store-pricing-heatmap'
        else:
            title = f'Pricing Overlap Between Stores for {company_name} (Average Percentage)'
            filename_suffix = f'{company_name.lower()}-store-pricing-heatmap'

    plt.title(title)
    plt.xlabel(entity_type.capitalize())
    plt.ylabel(entity_type.capitalize())
    plt.tight_layout()
    
    # Define output directories and create them if they don't exist
    base_output_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'analysis')
    heatmap_output_dir = os.path.join(base_output_dir, 'heatmap')

    os.makedirs(base_output_dir, exist_ok=True)
    os.makedirs(heatmap_output_dir, exist_ok=True)

    # Generate a timestamp for unique filenames
    timestamp_str = datetime.now().strftime('%Y-%m-%d')
    
    png_filename = os.path.join(heatmap_output_dir, f'{timestamp_str}-{filename_suffix}.png')
    plt.savefig(png_filename)
    print(f"    Heatmap image saved to '{png_filename}'")
