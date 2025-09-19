
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

    if company.name.lower() == 'woolworths' and stores_with_products > 1:
        # --- WOOLWORTHS SPECIAL LOGIC (ONE-VS-ALL) ---
        print("    Applying special logic for Woolworths: comparing against largest store only.")
        main_store_name = max(store_products, key=lambda k: len(store_products[k]))
        main_store_products = store_products[main_store_name]
        other_stores = {k: v for k, v in store_products.items() if k != main_store_name}
        print(f"    - Largest store found: {main_store_name} ({len(main_store_products)} products)")

        # Calculate overall average
        overall_overlaps = []
        for other_name, other_prods in other_stores.items():
            intersection_len = len(main_store_products.intersection(other_prods))
            len_main = len(main_store_products)
            len_other = len(other_prods)
            p1 = intersection_len / len_main if len_main > 0 else 0
            p2 = intersection_len / len_other if len_other > 0 else 0
            overall_overlaps.append((p1 + p2) / 2)
        average_percentage_shared = np.mean(overall_overlaps) if overall_overlaps else 0

        # Category analysis
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

            main_store_cat_prods = main_store_products.intersection(category_product_ids)
            
            cat_overlaps = []
            detailed_report_content += f"\nCategory: {category.name}\n"
            for other_name, other_prods in other_stores.items():
                other_store_cat_prods = other_prods.intersection(category_product_ids)

                # Only compare if the other store has products in this category
                if not other_store_cat_prods:
                    continue
                
                intersection_len = len(main_store_cat_prods.intersection(other_store_cat_prods))
                len_main_cat = len(main_store_cat_prods)
                len_other_cat = len(other_store_cat_prods)

                p1 = intersection_len / len_main_cat if len_main_cat > 0 else 0
                p2 = intersection_len / len_other_cat if len_other_cat > 0 else 0
                avg_p = (p1 + p2) / 2
                cat_overlaps.append(avg_p)
                detailed_report_content += f"  - {main_store_name} / {other_name}: {avg_p:.2%}\n"

            category_analysis[category.name] = np.mean(cat_overlaps) if cat_overlaps else 0
            
            if command:
                command.stdout.write(f"\r    - Processing category: {category.name}... Done.\n")
                command.stdout.flush()

    elif stores_with_products > 1:
        # --- STANDARD LOGIC (ALL-VS-ALL) ---
        _, _, _, average_percentage_matrix = calculate_overlap_matrices(store_products, stdout=command.stdout if command else None)
        iu = np.triu_indices(average_percentage_matrix.shape[0], k=1)
        average_percentage_shared = np.mean(average_percentage_matrix.to_numpy()[iu]) if iu[0].size > 0 else 0

        print("    Analyzing categories...")
        if company.name.lower() == 'iga':
            level_name = "Tier 1"
            tier_0_categories_qs = Category.objects.filter(company=company, parents__isnull=True)
            start_categories = Category.objects.filter(parents__in=tier_0_categories_qs).distinct()
        else:
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

            category_store_products = {store: prods.intersection(category_product_ids) for store, prods in store_products.items()}
            category_store_products = {k: v for k, v in category_store_products.items() if v}

            if len(category_store_products) > 1:
                _, _, _, cat_avg_matrix = calculate_overlap_matrices(category_store_products)
                iu_cat = np.triu_indices(cat_avg_matrix.shape[0], k=1)
                avg_cat_shared = np.mean(cat_avg_matrix.to_numpy()[iu_cat]) if iu_cat[0].size > 0 else 0
                category_analysis[category.name] = avg_cat_shared

                detailed_report_content += f"\nCategory: {category.name}\n"
                store_names = cat_avg_matrix.columns
                for i, j in zip(iu_cat[0], iu_cat[1]):
                    detailed_report_content += f"  - {store_names[i]} / {store_names[j]}: {cat_avg_matrix.iloc[i, j]:.2%}\n"
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
    report_content += f"Average product overlap between any two stores: {average_percentage_shared:.2%}\n"
    report_content += "---"
    report_content += f"Average product overlap for {level_name} Categories:\n"
    for category_name, avg_shared in sorted(category_analysis.items(), key=lambda item: item[1], reverse=True):
        report_content += f"  - {category_name}: {avg_shared:.2%}\n"

    if detailed_report_content:
        report_content += "\n--- Detailed Overlap per Category ---"
        report_content += detailed_report_content

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
