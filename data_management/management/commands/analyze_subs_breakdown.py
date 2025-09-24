from django.core.management.base import BaseCommand
from data_management.utils.analysis_utils.substitution_breakdown import generate_substitution_breakdown_report

class Command(BaseCommand):
    help = 'Generates a report on the average number of substitutes per product, broken down by company and substitution level.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting substitution breakdown analysis..."))
        
        report = generate_substitution_breakdown_report()
        
        self.stdout.write(report)
        
        self.stdout.write(self.style.SUCCESS("\nAnalysis complete."))
