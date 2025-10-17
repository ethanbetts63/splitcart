from collections import defaultdict
from django.db.models import Count
from companies.models import Category

def generate_category_product_count_report():
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

    # Sort the aggregated data by product count in descending order
    sorted_groups = sorted(category_groups.items(), key=lambda item: item[1]['product_count'], reverse=True)

    # Format the report
    for name, data in sorted_groups:
        count = data['product_count']
        companies = ", ".join(sorted(list(data['companies'])))
        report_lines.append(f"- {name} ({count} products): [{companies}]")

    return "\n".join(report_lines)
