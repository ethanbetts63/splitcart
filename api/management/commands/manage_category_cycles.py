from django.core.management.base import BaseCommand
from companies.models import Company
from api.database_updating_classes.category_cycle_manager import CategoryCycleManager

class Command(BaseCommand):
    help = 'Automatically detects and prunes cycles in all company category hierarchies.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Category Cycle Pruning for All Companies ---"))
        all_companies = Company.objects.all()

        if not all_companies.exists():
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in all_companies:
            # Instantiate the manager for each company and run the pruning
            manager = CategoryCycleManager(self, company)
            manager.prune_cycles()
        
        self.stdout.write(self.style.SUCCESS("\n--- All companies processed. ---"))
