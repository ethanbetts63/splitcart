import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime
from itertools import combinations
from collections import defaultdict

from products.models import Product
from companies.models import Company
from django.conf import settings

def generate_product_overlap_heatmap():
    """
    Analyzes the product overlap between companies and generates a co-occurrence matrix (heatmap).
    Saves the output as a CSV and a PNG image.
    """
    print("--- Generating Product Overlap Heatmap ---")

    # Get all companies
    companies = Company.objects.all()
    company_names = [c.name for c in companies]

    # Dictionary to hold sets of product IDs for each company
    company_products = defaultdict(set)

    print("    Fetching all products and their company relationships...")
    product_queryset = Product.objects.prefetch_related('prices__store__company').all()

    for product in product_queryset.iterator(chunk_size=500):
        product_companies = {price.store.company.name for price in product.prices.all()}
        for company_name in product_companies:
            company_products[company_name].add(product.id)
    
    print("    Calculating co-occurrence matrix...")
    # Create empty DataFrames for raw counts and percentages
    overlap_matrix = pd.DataFrame(0, index=company_names, columns=company_names)
    percent_of_row_matrix = pd.DataFrame(0.0, index=company_names, columns=company_names)
    percent_of_col_matrix = pd.DataFrame(0.0, index=company_names, columns=company_names)
    average_percentage_matrix = pd.DataFrame(0.0, index=company_names, columns=company_names)

    # Calculate the overlap (intersection) for each pair of companies
    for company1, company2 in combinations(company_names, 2):
        intersection_size = len(company_products[company1].intersection(company_products[company2]))
        
        total_products_c1 = len(company_products[company1])
        total_products_c2 = len(company_products[company2])

        # Raw counts
        overlap_matrix.loc[company1, company2] = intersection_size
        overlap_matrix.loc[company2, company1] = intersection_size

        # Percentages
        percent_c1_in_c2 = (intersection_size / total_products_c1) * 100 if total_products_c1 > 0 else 0
        percent_c2_in_c1 = (intersection_size / total_products_c2) * 100 if total_products_c2 > 0 else 0

        percent_of_row_matrix.loc[company1, company2] = percent_c1_in_c2
        percent_of_col_matrix.loc[company1, company2] = percent_c2_in_c1

        percent_of_row_matrix.loc[company2, company1] = percent_c2_in_c1 # Note the swap for symmetry
        percent_of_col_matrix.loc[company2, company1] = percent_c1_in_c2 # Note the swap for symmetry

        # Average percentage
        average_percentage_matrix.loc[company1, company2] = (percent_c1_in_c2 + percent_c2_in_c1) / 2
        average_percentage_matrix.loc[company2, company1] = (percent_c1_in_c2 + percent_c2_in_c1) / 2

    # Fill the diagonal for raw counts (total unique products for each company)
    for company_name in company_names:
        total_unique = len(company_products[company_name])
        overlap_matrix.loc[company_name, company_name] = total_unique
        percent_of_row_matrix.loc[company_name, company_name] = 100.0
        percent_of_col_matrix.loc[company_name, company_name] = 100.0
        average_percentage_matrix.loc[company_name, company_name] = 100.0

    # Define output directories and create them if they don't exist
    base_output_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'analysis')
    heatmap_output_dir = os.path.join(base_output_dir, 'heatmap')

    os.makedirs(base_output_dir, exist_ok=True)
    os.makedirs(heatmap_output_dir, exist_ok=True)

    # Generate a timestamp for unique filenames
    timestamp_str = datetime.now().strftime('%Y-%m-%d')

    # Custom annotation function for heatmap
    def annot_format(val, row_idx, col_idx):
        company1 = overlap_matrix.index[row_idx]
        company2 = overlap_matrix.columns[col_idx]
        
        raw_count = overlap_matrix.loc[company1, company2]
        percent_row = percent_of_row_matrix.loc[company1, company2]
        percent_col = percent_of_col_matrix.loc[company1, company2]

        if company1 == company2:
            return f"Total: {raw_count}\n100%"
        else:
            return f"Count: {raw_count}\n% of {company1}: {percent_row:.1f}%\n% of {company2}: {percent_col:.1f}%"

    # Generate and save the heatmap
    print("    Generating heatmap image...")
    plt.figure(figsize=(16, 14)) # Increased size for more text
    sns.heatmap(average_percentage_matrix, annot=True, fmt='', cmap='viridis', cbar=True, 
                xticklabels=True, yticklabels=True, 
                annot_kws={"fontsize":8})

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

    plt.title('Product Overlap Between Companies (Average Percentage)')
    plt.xlabel('Company')
    plt.ylabel('Company')
    plt.tight_layout()
    
    png_filename = os.path.join(heatmap_output_dir, f'{timestamp_str}-company-heatmap.png')
    plt.savefig(png_filename)
    print(f"    Heatmap image saved to '{png_filename}'")
    print("--- Finished ---")