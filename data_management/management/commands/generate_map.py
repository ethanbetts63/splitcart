from django.core.management.base import BaseCommand
from data_management.utils.analysis_utils.map_generator import generate_store_map

class Command(BaseCommand):
    help = 'Generates a map of store locations, optionally filtered by company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='The name of a specific company to generate a map for.'
        )

    def handle(self, *args, **options):
        company_name = options.get('company')
        
        if company_name:
            self.stdout.write(f"Generating store location map for {company_name}...")
        else:
            self.stdout.write("Generating store location map for all companies...")
        
        output_file = generate_store_map(company_name=company_name)
        
        if output_file:
            self.stdout.write(self.style.SUCCESS(f"Successfully generated map: {output_file}"))
        else:
            self.stdout.write(self.style.ERROR("Map generation failed. See previous messages for details."))
