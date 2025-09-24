from companies.models import Company
from products.models import Product, ProductSubstitution
from django.db.models import Q

def generate_substitution_breakdown_report():
    """
    Analyzes the substitution landscape for each company, calculating the average
    number of substitutes per product at each substitution level.
    """
    report_lines = ["--- Substitution Breakdown Analysis ---"]
    companies = Company.objects.all().order_by('name')

    # Get all substitution levels from the model definition
    levels = [level[0] for level in ProductSubstitution.SUBSTITUTION_LEVELS]

    print("Analyzing companies...")
    for company in companies:
        report_lines.append(f"\n--- Analysis for: {company.name} ---")
        
        # Get all unique products for this company
        company_products = Product.objects.filter(prices__store__company=company).distinct()
        num_products = company_products.count()

        if num_products == 0:
            report_lines.append("  No products found for this company.")
            continue
            
        report_lines.append(f"  Total unique products: {num_products}")

        print(f"  - Analyzing levels for {company.name}...")
        for level in levels:
            # Count substitutions where product_a is in the company's product list
            count_a = ProductSubstitution.objects.filter(
                level=level,
                product_a__in=company_products
            ).count()
            
            # Count substitutions where product_b is in the company's product list
            count_b = ProductSubstitution.objects.filter(
                level=level,
                product_b__in=company_products
            ).count()

            # The total number of substitution connections for products in this company.
            # This correctly sums the degrees of all nodes belonging to this company in the substitution graph.
            total_connections = count_a + count_b
            
            avg_subs_per_product = total_connections / num_products if num_products > 0 else 0
            report_lines.append(f"  - {level}: Average {avg_subs_per_product:.2f} substitutes per product.")

    return "\n".join(report_lines)
