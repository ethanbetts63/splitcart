import os
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Product, ProductSubstitution

class Command(BaseCommand):
    help = 'Analyzes product substitutions and saves the report to a file.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Substitution Analysis ---"))

        HUB_COUNT = 20
        SAMPLE_SIZE = 20

        report_parts = []
        report_parts.append(self._get_overall_stats_text())
        report_parts.append(self._get_hub_products_text(HUB_COUNT))

        # Get distinct substitution types from the database
        sub_types = ProductSubstitution.objects.values_list('type', flat=True).distinct()

        for sub_type in sub_types:
            report_parts.append(self._get_random_samples_text(SAMPLE_SIZE, sub_type))

        # --- File Output ---
        report_content = "\n\n".join(report_parts)
        
        # Construct the path relative to the project root
        output_dir = os.path.join('api', 'data', 'analysis', 'subs')
        os.makedirs(output_dir, exist_ok=True)
        
        file_name = f"{datetime.date.today()}-subs_analysis.txt"
        file_path = os.path.join(output_dir, file_name)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully wrote analysis report to: {file_path}"))
        except IOError as e:
            self.stderr.write(self.style.ERROR(f"Error writing to file: {e}"))

    def _get_overall_stats_text(self):
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

        lines.append("\n--- Substitutions by Type ---")
        type_counts = ProductSubstitution.objects.values('type').annotate(count=Count('type')).order_by('-count')
        for item in type_counts:
            percentage = (item['count'] / total_substitutions) * 100
            lines.append(f"- {item['type']}: {item['count']} ({percentage:.2f}%)")
        
        return "\n".join(lines)

    def _get_hub_products_text(self, hub_count):
        lines = [f"--- Top {hub_count} Substitution Hubs ---"]
        
        hub_products = Product.objects.annotate(
            num_subs=Count('substitutions_a', distinct=True) + Count('substitutions_b', distinct=True)
        ).order_by('-num_subs')[:hub_count]

        for i, product in enumerate(hub_products):
            lines.append(f"  {i+1}. \"{product.name}\" ({product.brand}) - {product.num_subs} links")
        
        return "\n".join(lines)

    def _get_random_samples_text(self, sample_size, sub_type):
        lines = [f"--- Random Sample of {sample_size} Substitutions (Type: {sub_type.upper()}) ---"]

        queryset = ProductSubstitution.objects.filter(type__iexact=sub_type)

        if queryset.count() == 0:
            lines.append("No substitutions found for this type.")
            return "\n".join(lines)

        random_samples = queryset.order_by('?')[:sample_size]

        for i, sub in enumerate(random_samples):
            lines.append(f"\n--- Sample {i+1}/{sample_size} (Score: {sub.score}) ---")
            lines.append(f"  [A] Name: {sub.product_a.name} | Brand: {sub.product_a.brand} | Sizes: {sub.product_a.sizes}")
            lines.append(f"  [B] Name: {sub.product_b.name} | Brand: {sub.product_b.brand} | Sizes: {sub.product_b.sizes}")
            
        return "\n".join(lines)