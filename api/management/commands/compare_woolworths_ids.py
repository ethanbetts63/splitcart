import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Compares store IDs found by the two Woolworths scrapers.'

    def handle(self, *args, **options):
        file1 = 'woolworths1_ids.txt'
        file2 = 'woolworths2_ids.txt'

        if not os.path.exists(file1) or not os.path.exists(file2):
            self.stdout.write(self.style.ERROR(f"Error: Make sure both {file1} and {file2} exist in the root directory."))
            self.stdout.write(self.style.WARNING("You need to run both Woolworths store scrapers first to generate these files."))
            return

        self.stdout.write(f"Reading IDs from {file1} and {file2}...")

        with open(file1, 'r') as f:
            ids1 = set(line.strip() for line in f if line.strip())
        
        with open(file2, 'r') as f:
            ids2 = set(line.strip() for line in f if line.strip())

        self.stdout.write(f"Found {len(ids1)} unique IDs in {file1}")
        self.stdout.write(f"Found {len(ids2)} unique IDs in {file2}")

        common_ids = ids1.intersection(ids2)
        unique_to_1 = ids1 - ids2
        unique_to_2 = ids2 - ids1

        self.stdout.write(self.style.SUCCESS("\n--- Comparison Results ---"))
        self.stdout.write(f"Stores found by BOTH scrapers: {len(common_ids)}")
        self.stdout.write(f"Stores found ONLY by scraper 1 (geolocation): {len(unique_to_1)}")
        self.stdout.write(f"Stores found ONLY by scraper 2 (postcode): {len(unique_to_2)}")

        if unique_to_2:
            self.stdout.write(self.style.WARNING("\nScraper 2 (postcode) found unique stores. It seems valuable to keep."))
            self.stdout.write("A few examples of unique IDs found only by scraper 2:")
            for i, store_id in enumerate(list(unique_to_2)[:5]):
                self.stdout.write(f" - {store_id}")
        elif not unique_to_2 and common_ids:
             self.stdout.write(self.style.SUCCESS("\nScraper 2 (postcode) did not find any unique stores. It may be redundant."))
        else:
            self.stdout.write(self.style.WARNING("\nNo conclusions can be drawn yet. Ensure scrapers have run long enough."))
