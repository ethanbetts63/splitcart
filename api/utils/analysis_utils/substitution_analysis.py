import os
import datetime
from collections import defaultdict
from django.db.models import Count
from products.models import Product, ProductSubstitution

def generate_substitution_analysis_report():
    """
    Analyzes product substitutions and returns the report as a string.
    """
    report_parts = []
    report_parts.append(_get_overall_stats_text())
    report_parts.append(_get_hub_products_text(20))

    for level in range(1, 5):
        report_parts.append(_get_random_samples_text(20, level))

    return "\n\n".join(report_parts)

def _get_overall_stats_text():
    lines = ["--- Overall Substitution Statistics ---"]
    total_products = Product.objects.count()
    total_substitutions = ProductSubstitution.objects.count()

    if total_substitutions == 0:
        lines.append("No substitutions found in the database.")
        return "\n".join(lines)

    products_in_subs_a = ProductSubstitution.objects.values_list('product_a_id', flat=True)
    products_in_subs_b = ProductSubstitution.objects.values_list('product_b_id', flat=True)
    products_with_subs_count = len(set(list(products_in_subs_a) + list(products_in_subs_b)))

    lines.append(f"- Total Products in DB: {total_products}")
    lines.append(f"- Total Substitution Links: {total_substitutions}")
    lines.append(f"- Products with at least one substitute: {products_with_subs_count} ({products_with_subs_count/total_products:.2%})")

    lines.append("\n--- Substitutions by Level ---")
    type_counts = ProductSubstitution.objects.values('type').annotate(count=Count('type'))
    level_counts = {
        1: 0,
        2: 0,
        3: 0,
        4: 0
    }
    for item in type_counts:
        if item['type'] in ['STRICT', 'SIZE']:
            level_counts[1] += item['count']
        elif item['type'] == 'SIMILAR_PRODUCT':
            level_counts[2] += item['count']
        elif item['type'] == 'CROSS_BRAND_SIMILAR_PRODUCT':
            level_counts[3] += item['count']
        elif item['type'] == 'CROSS_BRAND_DIFFERENT_SIZE':
            level_counts[4] += item['count']

    definitions = {
        1: 'Same brand, same product, different size.',
        2: 'Same brand, similar product, similar size.',
        3: 'Different brand, similar product, similar size.',
        4: 'Different brand, similar product, different size.'
    }

    for level, count in sorted(level_counts.items()):
        if count > 0:
            percentage = (count / total_substitutions) * 100
            lines.append(f"- Level {level}: {definitions[level]} - {count} ({percentage:.2f}%)")
    
    return "\n".join(lines)

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
    definitions = {
        1: 'Same brand, same product, different size.',
        2: 'Same brand, similar product, similar size.',
        3: 'Different brand, similar product, similar size.',
        4: 'Different brand, similar product, different size.'
    }
    definition = definitions.get(level, 'N/A')

    types_for_level = {
        1: ['STRICT', 'SIZE'],
        2: ['SIMILAR_PRODUCT'],
        3: ['CROSS_BRAND_SIMILAR_PRODUCT'],
        4: ['CROSS_BRAND_DIFFERENT_SIZE']
    }.get(level, [])

    header = f"--- Level {level}: {definition} ---"
    lines = [header]
    
    queryset = ProductSubstitution.objects.filter(type__in=types_for_level)

    if queryset.count() == 0:
        lines.append("No substitutions found for this level.")
        return "\n".join(lines)

    random_samples = queryset.order_by('?')[:sample_size]

    for i, sub in enumerate(random_samples):
        lines.append(f"\n--- Sample {i+1}/{sample_size} (Score: {sub.score}) ---")
        lines.append(f"  [A] Name: {sub.product_a.name} | Brand: {sub.product_a.brand} | Sizes: {sub.product_a.sizes}")
        lines.append(f"  [B] Name: {sub.product_b.name} | Brand: {sub.product_b.brand} | Sizes: {sub.product_b.sizes}")
        
    return "\n".join(lines)
