
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations
from collections import defaultdict
from products.models import Product
from companies.models import Company

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

    # This can be memory intensive if there are millions of products.
    # It fetches all products and their related store companies.
    print("    Fetching all products and their company relationships...")
    product_queryset = Product.objects.prefetch_related('prices__store__company').all()

    for product in product_queryset.iterator(chunk_size=500):
        product_companies = {price.store.company.name for price in product.prices.all()}
        for company_name in product_companies:
            company_products[company_name].add(product.id)
    
    print("    Calculating co-occurrence matrix...")
    # Create an empty DataFrame for the co-occurrence matrix
    overlap_matrix = pd.DataFrame(0, index=company_names, columns=company_names)

    # Calculate the overlap (intersection) for each pair of companies
    for company1, company2 in combinations(company_names, 2):
        intersection_size = len(company_products[company1].intersection(company_products[company2]))
        overlap_matrix.loc[company1, company2] = intersection_size
        overlap_matrix.loc[company2, company1] = intersection_size

    # Fill the diagonal with the total number of unique products for each company
    for company_name in company_names:
        overlap_matrix.loc[company_name, company_name] = len(company_products[company_name])

    # Save the matrix to a CSV file
    csv_filename = 'product_overlap_matrix.csv'
    overlap_matrix.to_csv(csv_filename)
    print(f"    Overlap matrix saved to '{csv_filename}'")

    # Generate and save the heatmap
    print("    Generating heatmap image...")
    plt.figure(figsize=(12, 10))
    sns.heatmap(overlap_matrix, annot=True, fmt='d', cmap='viridis')
    plt.title('Product Overlap Between Companies')
    plt.xlabel('Company')
    plt.ylabel('Company')
    plt.tight_layout()
    
    png_filename = 'product_overlap_heatmap.png'
    plt.savefig(png_filename)
    print(f"    Heatmap image saved to '{png_filename}'")
    print("--- Finished ---")

