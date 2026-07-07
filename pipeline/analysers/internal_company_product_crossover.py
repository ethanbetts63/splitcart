
import os
import datetime
import numpy as np
from companies.models import Company, Category
from products.models import Product
from pipeline.utils.analysis_utils.product_overlap.get_product_sets_by_entity import get_product_sets_by_entity
from pipeline.utils.analysis_utils.product_overlap.calculate_overlap_matrices import calculate_overlap_matrices

def generate_internal_company_product_crossover_report(company_name, command=None):
    """
    Analyzes product coverage for a specific company and generates a text report.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company with name '{company_name}' not found.")
        return

    print(f"--- Generating Internal Company Product Crossover Report for {company.name} ---")

    # Get all products for the company
    print("    Fetching all products for company...")
    all_products = Product.objects.filter(prices__company=company).distinct()
    total_products = all_products.count()

    print("    Fetching product set for company...")
    company_products = get_product_sets_by_entity(entity_type='company')
    entity_products = {
        company.name: company_products.get(company.name, set())
    }
    companies_with_products = 1 if entity_products[company.name] else 0

    # Database fullness
    database_fullness = f"{companies_with_products} / 1"

    # --- Analysis Section ---
    average_percentage_shared = 0
    category_analysis = {}
    detailed_report_content = ""
    level_name = "Tier 0"

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

    if len(entity_products) > 1:
        _, _, _, average_percentage_matrix = calculate_overlap_matrices(entity_products, stdout=command.stdout if command else None)
        iu = np.triu_indices(average_percentage_matrix.shape[0], k=1)
        average_percentage_shared = np.mean(average_percentage_matrix.to_numpy()[iu]) if iu[0].size > 0 else 0

        print("    Analyzing categories...")
        start_categories = Category.objects.filter(company=company, parents__isnull=True)

        for category in start_categories:
            if command:
                command.stdout.write(f"    - Processing category: {category.name}...")
                command.stdout.flush()
            
            descendant_categories = get_all_descendants(category)
            category_product_ids = set(all_products.filter(category__in=descendant_categories).values_list('id', flat=True))

            if not category_product_ids:
                category_analysis[category.name] = 0
                continue

            category_company_products = {name: prods.intersection(category_product_ids) for name, prods in entity_products.items()}
            category_company_products = {k: v for k, v in category_company_products.items() if v}

            if len(category_company_products) > 1:
                _, _, _, cat_avg_matrix = calculate_overlap_matrices(category_company_products)
                iu_cat = np.triu_indices(cat_avg_matrix.shape[0], k=1)
                avg_cat_shared = np.mean(cat_avg_matrix.to_numpy()[iu_cat]) if iu_cat[0].size > 0 else 0
                category_analysis[category.name] = avg_cat_shared

                detailed_report_content += f"\nCategory: {category.name}\n"
                company_names = cat_avg_matrix.columns
                for i, j in zip(iu_cat[0], iu_cat[1]):
                    detailed_report_content += f"  - {company_names[i]} / {company_names[j]}: {cat_avg_matrix.iloc[i, j]:.2%}\n"
            else:
                category_analysis[category.name] = 0

            if command:
                command.stdout.write(f"\r    - Processing category: {category.name}... Done.\n")
                command.stdout.flush()

    # --- Report Assembly ---
    report_content = f"Internal Company Product Crossover Report for: {company.name}\n"
    report_content += f"Generated on: {datetime.date.today()}\n"
    report_content += "---"
    report_content += f"Total unique products for {company.name}: {total_products}\n"
    report_content += f"Database fullness: {database_fullness}\n"
    report_content += f"Average product overlap between compared companies: {average_percentage_shared:.2%}\n"
    report_content += "---"
    report_content += f"Average product overlap for {level_name} Categories:\n"
    for category_name, avg_shared in sorted(category_analysis.items(), key=lambda item: item[1], reverse=True):
        report_content += f"  - {category_name}: {avg_shared:.2%}\n"

    if detailed_report_content:
        report_content += "\n--- Detailed Overlap per Category ---"
        report_content += detailed_report_content

    # Write report to file
    output_dir = os.path.join('pipeline', 'data', 'analysis', 'internal_company_product_crossover')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{company.name.lower()}_product_crossover.txt")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Successfully wrote analysis report to: {file_path}")
    except IOError as e:
        print(f"Error writing to file: {e}")

    print("--- Finished ---")
