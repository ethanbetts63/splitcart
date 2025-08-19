import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from companies.models import Store, Company, Category
from products.models import Product, Price
from django.db.models import Count, Q

def generate_category_price_correlation_heatmap(company_name, category_name):
    """
    Generates a heatmap showing the percentage of identically priced products
    for a specific category across all stores of a company.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company '{company_name}' not found.")
        return

    try:
        # Assuming category names are unique within a company
        category = Category.objects.get(name__iexact=category_name, company=company)
    except Category.DoesNotExist:
        print(f"Category '{category_name}' not found for company '{company_name}'.")
        return

    stores = Store.objects.filter(company=company).annotate(
        product_count=Count('prices__product', filter=Q(prices__product__category=category))
    ).filter(product_count__gt=100)
    store_count = stores.count()
    if store_count < 2:
        print(f"Skipping category '{category_name}': Not enough stores with over 100 products in this category.")
    else:
        # Create a DataFrame to store the correlation matrix
        correlation_matrix = pd.DataFrame(index=[s.store_name for s in stores], columns=[s.store_name for s in stores], dtype=float)

        total_comparisons = store_count * (store_count - 1) // 2
        current_comparison = 0

        for i in range(store_count):
            for j in range(i, store_count):
                store1 = stores[i]
                store2 = stores[j]

                if i == j:
                    correlation_matrix.iloc[i, j] = 100.0
                    continue

                current_comparison += 1
                print(f"Comparing stores: {store1.store_name} and {store2.store_name} ({current_comparison}/{total_comparisons})")

                # Get all products in the category for each store
                products1 = set(Product.objects.filter(category=category, prices__store=store1).values_list('id', flat=True))
                products2 = set(Product.objects.filter(category=category, prices__store=store2).values_list('id', flat=True))

                common_product_ids = products1.intersection(products2)
                
                if not common_product_ids:
                    percentage = 0.0
                else:
                    identical_price_count = 0
                    for product_id in common_product_ids:
                        try:
                            price1 = Price.objects.get(product_id=product_id, store=store1).price
                            price2 = Price.objects.get(product_id=product_id, store=store2).price
                            if price1 is not None and price1 == price2:
                                identical_price_count += 1
                        except Price.DoesNotExist:
                            continue
                    
                    percentage = (identical_price_count / len(common_product_ids)) * 100 if len(common_product_ids) > 0 else 0.0

                correlation_matrix.loc[store1.store_name, store2.store_name] = percentage
                correlation_matrix.loc[store2.store_name, store1.store_name] = percentage

        # Generate the heatmap
        plt.figure(figsize=(15, 12))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".1f")
        plt.title(f'Identically Priced Product Percentage for Category: {category_name} in {company_name}')
        plt.xlabel('Store')
        plt.ylabel('Store')
        
        # Save the heatmap
        output_dir = os.path.join('api', 'data', 'analysis')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = f'{company_name.lower()}_{category_name.lower()}_category_price_correlation_heatmap.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath)
        print(f"Heatmap saved to {filepath}")