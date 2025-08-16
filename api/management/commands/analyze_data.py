
from django.core.management.base import BaseCommand
from api.utils.analysis_utils.company_analysis import generate_store_product_counts_chart
from api.utils.analysis_utils.product_analysis import generate_product_overlap_heatmap

class Command(BaseCommand):
    help = 'Generates various reports and visualizations from product data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            type=str,
            required=True,
            help='Specifies which type of analysis or report to generate.',
            choices=['store_product_counts', 'overlap_heatmap']
        )
        parser.add_argument(
            '--company',
            type=str,
            help='The name of the company to generate the report for (required for some reports).'
        )

    def handle(self, *args, **options):
        report_type = options['report']
        company_name = options['company']

        if report_type == 'store_product_counts':
            if not company_name:
                self.stdout.write(self.style.ERROR(
                    'The --company argument is required for the store_product_counts report.'))
                return
            self.stdout.write(self.style.SUCCESS(
                f"Generating store product counts chart for '{company_name}'..."))
            generate_store_product_counts_chart(company_name)
        
        elif report_type == 'overlap_heatmap':
            generate_product_overlap_heatmap()

        else:
            self.stdout.write(self.style.WARNING(
                f"Report type '{report_type}' is not yet implemented."))

