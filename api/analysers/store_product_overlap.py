from api.utils.analysis_utils.product_overlap.get_product_sets_by_entity import get_product_sets_by_entity
from api.utils.analysis_utils.product_overlap.calculate_overlap_matrices import calculate_overlap_matrices
from api.utils.analysis_utils.product_overlap.generate_heatmap_image import generate_heatmap_image
from companies.models import Company

def generate_store_product_overlap_heatmap(company_name):
    """
    Analyzes the product overlap between stores of a specific company and generates a co-occurrence matrix (heatmap).
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company with name '{company_name}' not found.")
        return

    print(f"--- Generating Store Product Overlap Heatmap for {company.name} ---")

    # 1. Get product sets for all stores in the company
    store_products = get_product_sets_by_entity(entity_type='store', company_name=company.name)

    if not store_products:
        print(f"No stores with products found for {company.name}.")
        return

    # 2. Calculate overlap matrices
    overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix = calculate_overlap_matrices(store_products)

    # 3. Generate and save the heatmap image
    generate_heatmap_image(overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix, entity_type='store', company_name=company.name)

    print("--- Finished ---")
