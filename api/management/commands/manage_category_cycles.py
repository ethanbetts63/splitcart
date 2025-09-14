from django.core.management.base import BaseCommand
from companies.models import Company
from api.database_updating_classes.category_cycle_manager import CategoryCycleManager

class Command(BaseCommand):
    help = 'Detects and interactively repairs cycles in category hierarchies.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            required=True,
            help='The name of the company to diagnose.'
        )
        # In the future, we can add --repair and --detect-only flags

    def handle(self, *args, **options):
        company_name = options['company_name']
        try:
            company = Company.objects.get(name__iexact=company_name)
        except Company.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Company '{company_name}' not found."))
            return

        # Instantiate the manager and run the interactive repair
        manager = CategoryCycleManager(self, company)
        manager.repair_cycles_interactive()
