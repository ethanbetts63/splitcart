from products.models import SuperCategory
from companies.models import Company
from django.db.models import Count

def generate_super_category_report():
    """Generates a report on super categories, their product counts, and associated companies and categories."""
    report_lines = []
    super_cats_data = []

    super_categories = SuperCategory.objects.prefetch_related(
        'categories', 
        'categories__products',
        'categories__company'
    ).annotate(
        product_count=Count('categories__products', distinct=True)
    ).order_by('-product_count')

    for sc in super_categories:
        companies = set()
        for category in sc.categories.all():
            if category.company:
                companies.add(category.company.name)
        
        sub_categories = sc.categories.all()

        super_cats_data.append({
            'name': sc.name,
            'product_count': sc.product_count,
            'companies': sorted(list(companies)),
            'sub_categories': sub_categories
        })

    for data in super_cats_data:
        report_lines.append(f"## Super Category: {data['name']}")
        report_lines.append(f"- Product Count: {data['product_count']}")
        report_lines.append(f"- Companies: {', '.join(data['companies'])}")
        report_lines.append("- Sub-categories:")
        for cat in data['sub_categories']:
            report_lines.append(f"  - {cat.name} (ID: {cat.id}, Company: {cat.company.name if cat.company else 'N/A'})")
        report_lines.append("\n")

    return "\n".join(report_lines)
