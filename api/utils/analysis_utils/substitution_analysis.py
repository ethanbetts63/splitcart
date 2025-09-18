import random
from collections import defaultdict
from django.db.models import Q, Count
from products.models import Product, ProductSubstitution
from companies.models import Company

def generate_substitution_analysis_report():
    """
    Analyzes product substitutions and returns the report as a string.
    """
    report_parts = []
    report_parts.append(_get_overall_stats_text())

    # --- Per-Company Breakdown ---
    companies = Company.objects.all().order_by('name')
    for company in companies:
        report_parts.append(_get_company_stats_text(company))

    # --- Hubs and Samples (Existing functionality is preserved) ---
    report_parts.append(_get_hub_products_text(20))

    levels = sorted([choice[0] for choice in ProductSubstitution.SUBSTITUTION_LEVELS])

    for level in levels:
        report_parts.append(_get_random_samples_text(20, level))

    return "\n\n".join(report_parts)

def _get_overall_stats_text():
    lines = ["--- Overall Substitution Statistics ---"]
    total_products = Product.objects.count()
    total_substitutions = ProductSubstitution.objects.count()

    if total_substitutions == 0:
        lines.append("No substitutions found in the database.")
        return "\n".join(lines)

    products_with_subs_count = Product.objects.annotate(
        num_subs=Count('substitutions_a') + Count('substitutions_b')
    ).filter(num_subs__gt=0).count()

    lines.append(f"- Total Products in DB: {total_products}")
    lines.append(f"- Total Substitution Links: {total_substitutions}")
    if total_products > 0:
        lines.append(f"- Products with at least one substitute: {products_with_subs_count} ({products_with_subs_count/total_products:.2%})")

    lines.append("\n--- Substitutions by Level (Overall) ---")
    level_choices = ProductSubstitution.SUBSTITUTION_LEVELS
    for level_code, level_desc in level_choices:
        count = ProductSubstitution.objects.filter(level=level_code).count()
        percentage = (count / total_substitutions) * 100 if total_substitutions > 0 else 0
        lines.append(f"- {level_desc} - {count} ({percentage:.2f}%)")
    
    return "\n".join(lines)

def _get_company_stats_text(company):
    report_lines = [f"--- Detailed Analysis for {company.name} ---"]
    
    # Get all unique products for this company
    company_products = Product.objects.filter(prices__store__company=company).distinct()
    if not company_products.exists():
        report_lines.append("  No products found for this company.")
        return "\n".join(report_lines)

    # --- Internal Substitutions ---
    report_lines.append("\n--- Internal Substitutions ({} <-> {}) ---".format(company.name, company.name))
    internal_subs_qs = ProductSubstitution.objects.filter(
        product_a__in=company_products, 
        product_b__in=company_products
    )
    total_internal_subs = internal_subs_qs.count()
    report_lines.append(f"  Total: {total_internal_subs}")

    if total_internal_subs > 0:
        level_choices = ProductSubstitution.SUBSTITUTION_LEVELS
        for level_code, level_desc in level_choices:
            count = internal_subs_qs.filter(level=level_code).count()
            percentage = (count / total_internal_subs) * 100
            report_lines.append(f"  - {level_desc} - {count} ({percentage:.2f}%)")

    # --- Cross-Company Substitutions ---
    report_lines.append("\n--- Cross-Company Substitutions ({} <-> Other) ---".format(company.name))
    
    # Find substitutions where one product is in the company's set and the other is not.
    cross_subs_qs = ProductSubstitution.objects.filter(
        (Q(product_a__in=company_products) & ~Q(product_b__in=company_products)) |
        (Q(product_b__in=company_products) & ~Q(product_a__in=company_products))
    ).distinct()
    
    total_cross_subs = cross_subs_qs.count()
    report_lines.append(f"  Total: {total_cross_subs}")

    if total_cross_subs > 0:
        level_choices = ProductSubstitution.SUBSTITUTION_LEVELS
        for level_code, level_desc in level_choices:
            count = cross_subs_qs.filter(level=level_code).count()
            percentage = (count / total_cross_subs) * 100
            report_lines.append(f"  - {level_desc} - {count} ({percentage:.2f}%)")
            
    return "\n".join(report_lines)

def _get_hub_products_text(hub_count):
    lines = [f"--- Top {hub_count} Substitution Hubs (Grouped) ---"]
    
    adj_list = defaultdict(set)
    substitutions = ProductSubstitution.objects.all()
    for sub in substitutions:
        adj_list[sub.product_a_id].add(sub.product_b_id)
        adj_list[sub.product_b_id].add(sub.product_a_id)

    if not adj_list:
        lines.append("No substitution links to analyze.")
        return "\n".join(lines)

    visited = set()
    all_hubs = []
    for product_id in adj_list:
        if product_id not in visited:
            component = []
            q = [product_id]
            visited.add(product_id)
            head = 0
            while head < len(q):
                curr_id = q[head]
                head += 1
                component.append(curr_id)
                for neighbor_id in adj_list[curr_id]:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        q.append(neighbor_id)
            
            if not component:
                continue
            
            hub_in_component = max(component, key=lambda pid: len(adj_list.get(pid, [])))
            link_count = len(component) - 1
            if link_count > 0:
                all_hubs.append((hub_in_component, link_count))

    all_hubs.sort(key=lambda x: x[1], reverse=True)
    top_hubs_data = all_hubs[:hub_count]
    
    hub_product_ids = [hub_id for hub_id, count in top_hubs_data]
    hub_products = Product.objects.in_bulk(hub_product_ids)

    for i, (hub_id, count) in enumerate(top_hubs_data):
        product = hub_products.get(hub_id)
        if product:
            lines.append(f"  {i+1}. \"{product.name}\" ({product.brand}) - {count} links in group")
    
    return "\n".join(lines)

def _get_random_samples_text(sample_size, level):
    choices_dict = dict(ProductSubstitution._meta.get_field('level').choices)
    level_display = choices_dict.get(level)
    header = f"--- Level {level.replace('LVL', '')}: {level_display} ---"
    lines = [header]

    queryset = ProductSubstitution.objects.filter(level=level)
    if not queryset.exists():
        lines.append("No substitutions found for this level.")
        return "\n".join(lines)

    if level == 'LVL1':
        # ... (existing LVL1 logic remains the same)
        adj_list = defaultdict(set)
        for sub in queryset:
            adj_list[sub.product_a_id].add(sub.product_b_id)
            adj_list[sub.product_b_id].add(sub.product_a_id)

        visited = set()
        all_groups = []
        for product_id in adj_list:
            if product_id not in visited:
                component = []
                q = [product_id]
                visited.add(product_id)
                head = 0
                while head < len(q):
                    curr_id = q[head]
                    head += 1
                    component.append(curr_id)
                    for neighbor_id in adj_list[curr_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            q.append(neighbor_id)
                all_groups.append(component)
        
        random.shuffle(all_groups)
        
        for i, group in enumerate(all_groups[:sample_size]):
            lines.append(f"\n--- Group {i+1}/{len(all_groups[:sample_size])} ---")
            products_in_group = Product.objects.filter(id__in=group)
            for product in products_in_group:
                lines.append(f"  - Name: {product.name} | Brand: {product.brand} | Sizes: {product.sizes}")
    else:
        # New stratified sampling for LVL2
        score_buckets = {
            "High Confidence (Score > 0.95)": (0.95, 1.01), # 1.01 to be inclusive of 1.0
            "Medium Confidence (0.85-0.95)": (0.85, 0.95),
            "Low Confidence (0.7-0.85)": (0.7, 0.85),
            "Very Low Confidence (< 0.7)": (0.0, 0.7),
        }
        
        samples_per_bucket = sample_size // len(score_buckets)

        for bucket_name, (lower_bound, upper_bound) in score_buckets.items():
            bucket_samples = queryset.filter(
                score__gt=lower_bound, 
                score__lte=upper_bound
            ).order_by('?')[:samples_per_bucket]

            if bucket_samples:
                lines.append(f"\n--- {bucket_name} ---")
                for i, sub in enumerate(bucket_samples):
                    lines.append(f"  --- Sample {i+1}/{len(bucket_samples)} (Score: {sub.score:.2f}) ---")
                    lines.append(f"    [A] Name: {sub.product_a.name} | Brand: {sub.product_a.brand} | Sizes: {sub.product_a.sizes}")
                    lines.append(f"    [B] Name: {sub.product_b.name} | Brand: {sub.product_b.brand} | Sizes: {sub.product_b.sizes}")
            
    return "\n".join(lines)
