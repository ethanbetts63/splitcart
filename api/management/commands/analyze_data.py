from django.core.management.base import BaseCommand
from api.analysers.company_analysis import generate_store_product_counts_chart
from api.analysers.company_product_overlap import generate_company_product_overlap_heatmap
from api.analysers.store_product_overlap import generate_store_product_overlap_heatmap
from api.analysers.store_pricing_heatmap import generate_store_pricing_heatmap
from api.analysers.category_price_correlation import generate_category_price_correlation_heatmap
from companies.models import Company, Category

class Command(BaseCommand):
    help = 'Generates various reports and visualizations from product data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            type=str,
            required=True,
            help='Specifies which type of analysis or report to generate.',
            choices=['store_product_counts', 'company_heatmap', 'store_heatmap', 'pricing_heatmap', 'category_heatmap']
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

        else:
            self.stdout.write(self.style.WARNING(
                f"Report type '{report_type}' is not yet implemented."))
