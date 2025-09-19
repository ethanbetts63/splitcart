
import os
import datetime
import numpy as np
from companies.models import Company, Store, Category
from products.models import Product
from api.utils.analysis_utils.product_overlap.get_product_sets_by_entity import get_product_sets_by_entity
from api.utils.analysis_utils.product_overlap.calculate_overlap_matrices import calculate_overlap_matrices

def generate_internal_company_product_crossover_report(company_name, command=None):
    """
    Analyzes the product overlap between stores of a specific company and generates a text report.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company with name '{company_name}' not found.")
        return

    print(f"--- Generating Internal Company Product Crossover Report for {company.name} ---")

    # Get all products for the company
    print("    Fetching all products for stores in company...")
    all_products = Product.objects.filter(prices__store__company=company).distinct()
    total_products = all_products.count()

    # Get all stores for the company
    all_stores = Store.objects.filter(company=company)
    total_stores_in_db = all_stores.count()

    # Get product sets for all stores in the company
    print("    Fetching product sets for each store...")
    store_products = get_product_sets_by_entity(entity_type='store', company_name=company.name)
    stores_with_products = len(store_products)

    # Database fullness
    database_fullness = f"{stores_with_products} / {total_stores_in_db}"

    # Average percentage of goods present in store pair
    if len(store_products) > 1:
        _, _, _, average_percentage_matrix = calculate_overlap_matrices(store_products, stdout=command.stdout if command else None)
        # Exclude the diagonal (self-comparison) and calculate the mean of the upper triangle
        iu = np.triu_indices(average_percentage_matrix.shape[0], k=1)
        average_percentage_shared = np.mean(average_percentage_matrix.to_numpy()[iu]) if iu[0].size > 0 else 0
    else:
        average_percentage_shared = 0

    print("    Analyzing Tier 0 categories...")
    # Tier 0 category analysis
    tier_0_categories = Category.objects.filter(company=company, parents__isnull=True)
    category_analysis = {}

    def get_all_descendants(root_category):
        """Helper function to get all descendants for a category."""
        descendants = {root_category}
        queue = [root_category]
        while queue:
            current_cat = queue.pop(0)
            for child in current_cat.subcategories.all():
                if child not in descendants:
                    descendants.add(child)
                    queue.append(child)
        return descendants

    for category in tier_0_categories:
        # Get all descendant categories
        descendant_categories = get_all_descendants(category)
        
        # Get products for these categories
        category_products = all_products.filter(category__in=descendant_categories).distinct()
        
        if not category_products:
            category_analysis[category.name] = 0
            continue

        # Filter store_products to only include products from this category tree
        category_store_products = {}
        for store, products in store_products.items():
            category_store_products[store] = {p for p in products if p in category_products}

        # Filter out stores with no products from this category
        category_store_products = {k: v for k, v in category_store_products.items() if v}

        if len(category_store_products) > 1:
            _, _, _, cat_avg_matrix = calculate_overlap_matrices(category_store_products)
            iu_cat = np.triu_indices(cat_avg_matrix.shape[0], k=1)
            avg_cat_shared = np.mean(cat_avg_matrix.to_numpy()[iu_cat]) if iu_cat[0].size > 0 else 0
            category_analysis[category.name] = avg_cat_shared
        else:
            category_analysis[category.name] = 0

    # Prepare report content
    report_content = f"Internal Company Product Crossover Report for: {company.name}\n"
    report_content += f"Generated on: {datetime.date.today()}"
    report_content += "---\n"
    report_content += f"Total unique products for {company.name}: {total_products}\n"
    report_content += f"Database fullness: {database_fullness}\n"
    report_content += f"Average product overlap between any two stores: {average_percentage_shared:.2%}\n"
    report_content += "---\n"
    report_content += "Average product overlap for Tier 0 Categories:\n"
    for category_name, avg_shared in sorted(category_analysis.items(), key=lambda item: item[1], reverse=True):
        report_content += f"  - {category_name}: {avg_shared:.2%}\n"

    # Write report to file
    output_dir = os.path.join('api', 'data', 'analysis', 'internal_company_product_crossover')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{company.name.lower()}_product_crossover.txt")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Successfully wrote analysis report to: {file_path}")
    except IOError as e:
        print(f"Error writing to file: {e}")

    print("--- Finished ---")
