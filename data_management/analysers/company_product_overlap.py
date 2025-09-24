from data_management.utils.analysis_utils.product_overlap.get_product_sets_by_entity import get_product_sets_by_entity
from data_management.utils.analysis_utils.product_overlap.calculate_overlap_matrices import calculate_overlap_matrices
from data_management.utils.analysis_utils.product_overlap.generate_heatmap_image import generate_heatmap_image

def generate_company_product_overlap_heatmap():
    """
    Analyzes the product overlap between companies and generates a co-occurrence matrix (heatmap).
    """
    print("--- Generating Company Product Overlap Heatmap ---")

    # 1. Get product sets for all companies
    company_products = get_product_sets_by_entity(entity_type='company')

    # Filter out companies with less than 100 products
    original_company_count = len(company_products)
    company_products = {company: products for company, products in company_products.items() if len(products) >= 100}
    filtered_company_count = original_company_count - len(company_products)
    if filtered_company_count > 0:
        print(f"    Filtered out {filtered_company_count} companies with fewer than 100 products.")

    if not company_products:
        print("No companies with 100 or more products found.")
        return

    # 2. Calculate overlap matrices
    overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix = calculate_overlap_matrices(company_products)

    # 3. Generate and save the heatmap image
    generate_heatmap_image(overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix, entity_type='company')

    print("--- Finished ---")
