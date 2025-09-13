import os
import datetime
from django.core.management.base import BaseCommand
from api.analysers.company_analysis import generate_store_product_counts_chart
from api.analysers.company_product_overlap import generate_company_product_overlap_heatmap
from api.analysers.store_product_overlap import generate_store_product_overlap_heatmap
from api.analysers.store_pricing_heatmap import generate_store_pricing_heatmap
from api.analysers.category_price_correlation import generate_category_price_correlation_heatmap
from api.utils.analysis_utils.category_tree import generate_category_tree
from api.utils.analysis_utils.substitution_analysis import generate_substitution_analysis_report
from api.utils.analysis_utils.savings_benchmark import run_savings_benchmark
from api.utils.analysis_utils.substitution_overlap import calculate_strict_substitution_overlap_matrix, generate_substitution_heatmap_image
from companies.models import Company, Category, Store

class Command(BaseCommand):
    help = 'Generates various reports and visualizations from product data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            type=str,
            required=True,
            help='Specifies which type of analysis or report to generate.',
            choices=['store_product_counts', 'company_heatmap', 'store_heatmap', 'pricing_heatmap', 'category_heatmap', 'category_tree', 'subs', 'savings', 'sub_heatmap']
        )
        parser.add_argument(
            '--company-name',
            type=str,
            help='The name of the company to generate the report for (required for some reports).'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='The category to generate the report for (required for category_heatmap report).'
        )
        parser.add_argument(
            '--state',
            type=str,
            help='The state to generate the report for (optional, for store-level reports).'
        )

    def handle(self, *args, **options):
        report_type = options['report']
        company_name = options['company_name']
        category_name = options['category']
        state = options['state']

        if report_type == 'store_product_counts':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company-name argument is required for the store_product_counts report.'))
                return
            self.stdout.write(self.style.SUCCESS(
                f"Generating store product counts chart for '{company_name}'..."))
            generate_store_product_counts_chart(company_name)
        
        elif report_type == 'company_heatmap':
            generate_company_product_overlap_heatmap()

        elif report_type == 'store_heatmap':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company-name argument is required for the store_heatmap report.'))
                return
            generate_store_product_overlap_heatmap(company_name, state)

        elif report_type == 'pricing_heatmap':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company-name argument is required for the pricing_heatmap report.'))
                return
            generate_store_pricing_heatmap(company_name, state)

        elif report_type == 'sub_heatmap':
            self.stdout.write(self.style.SUCCESS("Generating strict substitution overlap heatmap for companies..."))
            overlap_matrix = calculate_strict_substitution_overlap_matrix()
            generate_substitution_heatmap_image(overlap_matrix)

        elif report_type == 'category_heatmap':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company-name argument is required for the category_heatmap report.'))
                return

            if category_name:
                self.stdout.write(self.style.SUCCESS(
                    f"Generating category pricing heatmap for '{company_name}' and category '{category_name}'..."))
                generate_category_price_correlation_heatmap(company_name, category_name)
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Generating category pricing heatmaps for all categories in '{company_name}'..."))
                try:
                    company = Company.objects.get(name__iexact=company_name)
                    categories = Category.objects.filter(company=company)
                    for category in categories:
                        self.stdout.write(self.style.SUCCESS(f"  Generating heatmap for category '{category.name}'..."))
                        generate_category_price_correlation_heatmap(company_name, category.name)
                except Company.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Company '{company_name}' not found."))

        elif report_type == 'category_tree':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company-name argument is required for the category_tree report.'))
                return
            self.stdout.write(self.style.SUCCESS(
                f"Generating category tree for '{company_name}'..."))
            tree_output = generate_category_tree(company_name)
            self.stdout.write(tree_output)

        elif report_type == 'subs':
            self.stdout.write(self.style.SUCCESS("--- Starting Substitution Analysis ---"))
            report_content = generate_substitution_analysis_report()
            
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

        elif report_type == 'savings':
            self.stdout.write(self.style.SUCCESS("Running savings benchmark..."))
            output_dir = os.path.join('api', 'data', 'analysis', 'savings')
            os.makedirs(output_dir, exist_ok=True)
            
            file_name = f"{datetime.date.today()}-savings.txt"
            file_path = os.path.join(output_dir, file_name)

            run_savings_benchmark(file_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully wrote benchmark report to: {file_path}"))

        else:
            self.stdout.write(self.style.WARNING(
                f"Report type '{report_type}' is not yet implemented."))