from django.core.management.base import BaseCommand
from api.analysers.company_analysis import generate_store_product_counts_chart
from api.analysers.company_product_overlap import generate_company_product_overlap_heatmap
from api.analysers.store_product_overlap import generate_store_product_overlap_heatmap

class Command(BaseCommand):
    help = 'Generates various reports and visualizations from product data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            type=str,
            required=True,
            help='Specifies which type of analysis or report to generate.',
            choices=['store_product_counts', 'company_heatmap', 'store_heatmap']
        )
        parser.add_argument(
            '--company-name',
            type=str,
            help='The name of the company to generate the report for (required for some reports).'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='The ID of the company to generate the report for (required for some reports).'
        )

    def handle(self, *args, **options):
        report_type = options['report']
        company_name = options['company_name']
        company_id = options['company_id']

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
            if not company_id:
                self.stdout.write(self.style.ERROR(
                    'The --company-id argument is required for the store_heatmap report.'))
                return
            generate_store_product_overlap_heatmap(company_id)

        else:
            self.stdout.write(self.style.WARNING(
                f"Report type '{report_type}' is not yet implemented."))