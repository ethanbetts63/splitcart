from django.core.management.base import BaseCommand
from data_management.utils.analysis_utils.cluster_visualizer import generate_cluster_map

class Command(BaseCommand):
    help = 'Generates a map visualizing the geographic clusters for a specific company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            required=True,
            help='The name of the company to visualize clusters for.'
        )

    def handle(self, *args, **options):
        company_name = options['company']
        
        self.stdout.write(f"Generating cluster visualization map for {company_name}...")
        
        output_file = generate_cluster_map(company_name=company_name)
        
        if output_file:
            self.stdout.write(self.style.SUCCESS(f"Successfully generated map: {output_file}"))
        else:
            self.stdout.write(self.style.ERROR("Map generation failed. See previous messages for details."))
