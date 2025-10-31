from django.core.management.base import BaseCommand
from data_management.utils.analysis_utils.map_generator import generate_store_map

class MapGenerator:
    def __init__(self, command, company_name=None):
        self.command = command
        self.company_name = company_name

    def run(self):
        if self.company_name:
            self.command.stdout.write(f"Generating store location map for {self.company_name}...")
        else:
            self.command.stdout.write("Generating store location map for all companies...")
        
        output_file = generate_store_map(company_name=self.company_name)
        
        if output_file:
            self.command.stdout.write(self.command.style.SUCCESS(f"Successfully generated map: {output_file}"))
        else:
            self.command.stdout.write(self.command.style.ERROR("Map generation failed. See previous messages for details."))
