
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from django.conf import settings
from products.models import Price, ProductSubstitution
from companies.models import Company

def calculate_company_substitution_overlap_matrix():
    """
    Calculates the substitution overlap matrix between all companies.
    The value at (row_A, col_B) represents the percentage of Company A's products
    that can be found (either directly or via substitute) in Company B's entire range.
    """
    print("    Calculating company substitution overlap matrix...")
    companies = Company.objects.all()
    company_names = [c.name for c in companies]
    matrix = pd.DataFrame(0.0, index=company_names, columns=company_names)

    # Pre-fetch all product ID sets for each company
    company_product_sets = {
        company.id: set(Price.objects.filter(store__company=company).values_list('product_id', flat=True))
        for company in companies
    }

    # Pre-fetch all substitution relationships
    all_subs = ProductSubstitution.objects.all().values_list('product_a_id', 'product_b_id')
    sub_map = {}
    for p1_id, p2_id in all_subs:
        if p1_id not in sub_map: sub_map[p1_id] = set()
        if p2_id not in sub_map: sub_map[p2_id] = set()
        sub_map[p1_id].add(p2_id)
        sub_map[p2_id].add(p1_id)

    for i, company_a in enumerate(companies):
        products_a = company_product_sets[company_a.id]
        if not products_a:
            continue

        print(f"      Processing company {i+1}/{len(companies)}: {company_a.name}")

        for company_b in companies:
            if company_a.id == company_b.id:
                matrix.loc[company_a.name, company_b.name] = 100.0
                continue

            products_b = company_product_sets[company_b.id]
            covered_count = 0

            for product_a_id in products_a:
                if product_a_id in products_b:
                    covered_count += 1
                    continue

                substitute_ids = sub_map.get(product_a_id, set())
                if not substitute_ids.isdisjoint(products_b):
                    covered_count += 1
            
            percentage = (covered_count / len(products_a)) * 100 if products_a else 0
            matrix.loc[company_a.name, company_b.name] = percentage
            
    return matrix

def calculate_substitution_overlap_matrix(stores):
    """
    Calculates the substitution overlap matrix for a given list of stores.
    The value at (row_A, col_B) represents the percentage of Store A's products
    that can be found (either directly or via substitute) at Store B.
    """
    print("    Calculating substitution overlap matrix...")
    store_names = [store.store_name for store in stores]
    matrix = pd.DataFrame(0.0, index=store_names, columns=store_names)

    # Pre-fetch all product ID sets for each store to optimize
    store_product_sets = {
        store.id: set(Price.objects.filter(store=store).values_list('product_id', flat=True))
        for store in stores
    }

    # Pre-fetch all substitution relationships to optimize
    all_subs = ProductSubstitution.objects.all().values_list('product_a_id', 'product_b_id')
    sub_map = {}  # Maps a product_id to a set of its substitute_ids
    for p1_id, p2_id in all_subs:
        if p1_id not in sub_map: sub_map[p1_id] = set()
        if p2_id not in sub_map: sub_map[p2_id] = set()
        sub_map[p1_id].add(p2_id)
        sub_map[p2_id].add(p1_id)

    # Iterate through each pair of stores to calculate the overlap
    for i, store_a in enumerate(stores):
        products_a = store_product_sets[store_a.id]
        if not products_a:
            continue

        print(f"      Processing store {i+1}/{len(stores)}: {store_a.store_name}")

        for store_b in stores:
            if store_a.id == store_b.id:
                matrix.loc[store_a.store_name, store_b.store_name] = 100.0
                continue

            products_b = store_product_sets[store_b.id]
            covered_count = 0

            for product_a_id in products_a:
                # Check for direct presence
                if product_a_id in products_b:
                    covered_count += 1
                    continue

                # Check for substitute presence
                substitute_ids = sub_map.get(product_a_id, set())
                if not substitute_ids.isdisjoint(products_b):
                    covered_count += 1
            
            percentage = (covered_count / len(products_a)) * 100 if products_a else 0
            matrix.loc[store_a.store_name, store_b.store_name] = percentage
            
    return matrix

def generate_substitution_heatmap_image(overlap_matrix, entity_type, company_name=None, state=None):
    """
    Generates and saves a substitution overlap heatmap image.
    """
    print("    Generating substitution heatmap image...")

    plt.figure(figsize=(16, 14))
    sns.heatmap(overlap_matrix, annot=True, fmt='.1f', cmap='viridis', cbar=True,
                xticklabels=True, yticklabels=True,
                annot_kws={"fontsize": 8})

    if entity_type == 'company':
        title = 'Substitution Overlap Between Companies (%)'
        filename_suffix = 'company-substitution-heatmap'
    else:
        state_str = f' in {state}' if state else ''
        title = f'Substitution Overlap Between Stores for {company_name}{state_str} (%)'
        filename_suffix = f'{company_name.lower()}{"-" + state.lower() if state else ''}-store-substitution-heatmap'

    plt.title(title)
    plt.xlabel(f"Store B (Percentage of Store A's products covered by Store B)")
    plt.ylabel('Store A')
    plt.tight_layout()
    
    # Define output directories
    output_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'analysis', 'heatmap')
    os.makedirs(output_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime('%Y-%m-%d')
    png_filename = os.path.join(output_dir, f'{timestamp_str}-{filename_suffix}.png')
    plt.savefig(png_filename)
    print(f"    Heatmap image saved to '{png_filename}'")
