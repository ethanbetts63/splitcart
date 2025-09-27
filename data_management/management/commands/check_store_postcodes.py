from django.core.management.base import BaseCommand
from companies.models import Store, Postcode

class Command(BaseCommand):
    help = 'Checks for postcodes associated with stores that are not present in the Postcode model.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Checking Store Postcode Consistency ---"))

        # 1. Get all unique postcodes from the Store model
        store_postcodes = set(Store.objects.values_list('postcode', flat=True).distinct())
        store_postcodes.discard(None) # Remove None entries if any
        store_postcodes.discard('')    # Remove empty string entries if any

        # 2. Get all unique postcodes from the Postcode model
        known_postcodes = set(Postcode.objects.values_list('postcode', flat=True).distinct())

        # 3. Find postcodes in stores that are not in the Postcode model
        missing_postcodes = store_postcodes - known_postcodes

        if missing_postcodes:
            self.stdout.write(self.style.WARNING("\nFound postcodes in Store data that are NOT in the Postcode model:"))
            for postcode in sorted(list(missing_postcodes)):
                store_count = Store.objects.filter(postcode=postcode).count()
                self.stdout.write(f"- {postcode} (attached to {store_count} stores)")
            self.stdout.write(self.style.WARNING("\nConsider importing these postcodes or correcting store data."))
        else:
            self.stdout.write(self.style.SUCCESS("\nAll store postcodes are present in the Postcode model. Consistency check passed."))

        self.stdout.write(self.style.SUCCESS("--- Consistency Check Complete ---"))
