
from api.utils.analysis_utils.pricing_analysis.get_product_prices_by_store import get_product_prices_by_store
from api.utils.analysis_utils.pricing_analysis.calculate_pricing_overlap_matrix import calculate_pricing_overlap_matrix
from api.utils.analysis_utils.pricing_analysis.generate_pricing_heatmap_image import generate_pricing_heatmap_image
from companies.models import Company

def generate_store_pricing_heatmap(company_name, state=None):
    """
    Analyzes the pricing overlap between stores of a specific company and generates a co-occurrence matrix (heatmap).
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company with name '{company_name}' not found.")
        return

    if state:
        print(f"--- Generating Store Pricing Heatmap for {company.name} in {state} ---")
    else:
        print(f"--- Generating Store Pricing Heatmap for {company.name} ---")

    # 1. Get product prices for all stores in the company
    store_product_prices = get_product_prices_by_store(company_name=company.name, state=state)

    # 2. Filter out stores with less than 100 products
    original_store_count = len(store_product_prices)
    store_product_prices = {store: products for store, products in store_product_prices.items() if len(products) >= 100}
    filtered_store_count = original_store_count - len(store_product_prices)
    if filtered_store_count > 0:
        print(f"    Filtered out {filtered_store_count} stores with fewer than 100 products.")

    if not store_product_prices:
        print(f"No stores with 100 or more products found for {company.name}.")
        return

    # 3. Calculate overlap matrix
    overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix = calculate_pricing_overlap_matrix(store_product_prices)

    # 4. Generate and save the heatmap image
    generate_heatmap_image(overlap_matrix, percent_of_row_matrix, percent_of_col_matrix, average_percentage_matrix, entity_type='store', company_name=company.name, state=state)

    print("--- Finished ---")
