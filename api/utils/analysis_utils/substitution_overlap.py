import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from django.conf import settings
from products.models import Price, ProductSubstitution
from companies.models import Company

def calculate_strict_substitution_overlap_matrix():
    """
    Calculates the strict substitution overlap matrix between all companies.
    The value at (row_A, col_B) represents the percentage of Company A's products
    that have at least one substitute available in Company B's entire range.
    It IGNORES cases where the identical product exists in both companies.
    """
    print("    Calculating strict substitution overlap matrix...")
    companies = Company.objects.all()
    company_names = [c.name for c in companies]
    matrix = pd.DataFrame(0.0, index=company_names, columns=company_names)

    # Pre-fetch all product ID sets for each company
    company_product_sets = {
        company.id: set(Price.objects.filter(store__company=company).values_list('price_record__product_id', flat=True))
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
                # A company's products can have substitutes within its own range.
                pass # Keep this calculation.

            products_b = company_product_sets[company_b.id]
            sub_covered_count = 0

            for product_a_id in products_a:
                substitute_ids = sub_map.get(product_a_id, set())
                # Check for intersection, but remove the original product_a_id from the check set
                # to ensure we are only matching on substitutes.
                if not substitute_ids.isdisjoint(products_b - {product_a_id}):
                    sub_covered_count += 1
            
            percentage = (sub_covered_count / len(products_a)) * 100 if products_a else 0
            matrix.loc[company_a.name, company_b.name] = percentage
            
    return matrix

def generate_substitution_heatmap_image(overlap_matrix):
    """
    Generates and saves a substitution overlap heatmap image.
    """
    print("    Generating substitution heatmap image...")

    plt.figure(figsize=(16, 14))
    sns.heatmap(overlap_matrix, annot=True, fmt='.1f', cmap='viridis', cbar=True,
                xticklabels=True, yticklabels=True,
                annot_kws={"fontsize": 10})

    title = 'Strict Substitution Overlap Between Companies (%)'
    filename_suffix = 'company-strict-substitution-heatmap'

    plt.title(title)
    plt.xlabel("Company B")
    plt.ylabel("Company A (X% of A's products have a substitute in B)")
    plt.tight_layout()
    
    output_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'analysis', 'heatmap')
    os.makedirs(output_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime('%Y-%m-%d')
    png_filename = os.path.join(output_dir, f'{timestamp_str}-{filename_suffix}.png')
    plt.savefig(png_filename)
    print(f"    Heatmap image saved to '{png_filename}'")