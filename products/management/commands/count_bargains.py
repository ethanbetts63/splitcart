from django.core.management.base import BaseCommand
from products.models.bargain import Bargain

class Command(BaseCommand):
    """
    A temporary management command to count the number of Bargain instances in the database.
    """
    help = 'Counts the total number of bargain instances in the system.'

    def handle(self, *args, **options):
        """
        The main logic for the command.
        """
        self.stdout.write("--- Checking for Bargain model ---")
        
        try:
            bargain_count = Bargain.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Found a total of {bargain_count} bargain instances in the database."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred while trying to count bargains: {e}"))
            self.stderr.write(self.style.WARNING("Please ensure the 'Bargain' model exists and that database migrations are up to date."))

        self.stdout.write("--- Count complete ---")
