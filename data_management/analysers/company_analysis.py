
import os
from django.conf import settings
import matplotlib.pyplot as plt
import seaborn as sns
from django.db.models import Count
from django.utils.text import slugify
from companies.models import Company


def generate_company_product_counts_chart(company_name: str):
    """
    Generates a bar chart showing the total number of priced products for a company
    of a specified company and saves it as a PNG.

    Args:
        company_name: The name of the company to analyze.
    """
    try:
        # Get the company object
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company '{company_name}' not found.")
        return

    company_with_count = Company.objects.filter(pk=company.pk) \
                                        .annotate(product_count=Count('prices')) \
                                        .first()

    if not company_with_count or company_with_count.product_count == 0:
        print(f"No prices found for company '{company_name}'.")
        return

    # Prepare data for plotting
    company_names = [company.name]
    product_counts = [company_with_count.product_count]

    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.barplot(x=product_counts, y=company_names, hue=company_names, palette='viridis', legend=False)
    
    plt.xlabel('Total Number of Products')
    plt.ylabel('Company')
    plt.title(f'Total Products for {company.name}')
    plt.tight_layout()

    # Define output directories and create them if they don't exist
    base_output_dir = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'analysis')
    heatmap_output_dir = os.path.join(base_output_dir, 'heatmap')

    os.makedirs(base_output_dir, exist_ok=True)
    os.makedirs(heatmap_output_dir, exist_ok=True)

    # Save the plot
    output_filename = f"{slugify(company.name)}_company_product_counts.png"
    output_path = os.path.join(heatmap_output_dir, output_filename)
    plt.savefig(output_path)
    print(f"Chart saved as '{output_path}'")
