
import matplotlib.pyplot as plt
import seaborn as sns
from django.db.models import Count
from companies.models import Company, Store

def generate_store_product_counts_chart(company_name: str):
    """
    Generates a bar chart showing the total number of products for each store
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

    # Get all stores for the company, annotated with the count of their products (price entries)
    stores_with_counts = Store.objects.filter(company=company) \
                                      .annotate(product_count=Count('prices')) \
                                      .filter(product_count__gt=0) \
                                      .exclude(name='N/A') \
                                      .order_by('-product_count')

    if not stores_with_counts.exists():
        print(f"No stores found for company '{company_name}'.")
        return

    # Prepare data for plotting
    store_names = [store.name for store in stores_with_counts]
    product_counts = [store.product_count for store in stores_with_counts]

    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.barplot(x=product_counts, y=store_names, palette='viridis')
    
    plt.xlabel('Total Number of Products')
    plt.ylabel('Store')
    plt.title(f'Total Products per Store for {company.name}')
    plt.tight_layout()

    # Save the plot
    output_filename = f"{company.name.lower().replace(' ', '_')}_store_product_counts.png"
    plt.savefig(output_filename)
    print(f"Chart saved as '{output_filename}'")

