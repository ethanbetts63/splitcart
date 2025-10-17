from collections import defaultdict
from django.db.models import Count
from companies.models import Category, PopularCategory

def generate_category_product_count_report(sort_alphabetically=False, strict_filter=False):
    """
    Analyzes categories to count products and list associated companies.
    Returns the report as a string.
    """
    report_lines = ["--- Category Product Count Analysis ---"]

    # Annotate each category with its product count
    categories_with_counts = Category.objects.annotate(product_count=Count('products'))

    # Group categories by name to aggregate data
    category_groups = defaultdict(lambda: {'product_count': 0, 'companies': set()})

    for category in categories_with_counts:
        group = category_groups[category.name]
        group['product_count'] += category.product_count
        group['companies'].add(category.company.name)

    # Apply strict filter if requested
    if strict_filter:
        popular_category_names = set(PopularCategory.objects.values_list('name', flat=True))
        category_groups = {
            name: data for name, data in category_groups.items()
            if name in popular_category_names
        }

    # Sort the aggregated data based on the argument
    if sort_alphabetically:
        sorted_groups = sorted(category_groups.items(), key=lambda item: item[0])
    else:
        sorted_groups = sorted(category_groups.items(), key=lambda item: item[1]['product_count'], reverse=True)

    # Format the report
    for name, data in sorted_groups:
        count = data['product_count']
        companies = ", ".join(sorted(list(data['companies'])))
        report_lines.append(f"- {name} ({count} products): [{companies}]")

    # Add CSV-style list of names at the end
    report_lines.append("\n--- CSV-style Category Names ---")
    csv_names = ",".join([f"'{name}'" for name, data in sorted_groups])
    report_lines.append(csv_names)

    return "\n".join(report_lines)
