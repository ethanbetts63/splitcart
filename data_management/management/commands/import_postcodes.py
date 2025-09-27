import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from companies.models import Postcode

class Command(BaseCommand):
    help = 'Imports Australian postcode data from a JSON file.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'postcodes.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Postcode data file not found at {file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Loading postcode data from {file_path}..."))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Error: Could not decode JSON from {file_path}. Please ensure it's valid JSON."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(data)} entries. Importing..."))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for entry in data:
            postcode_str = entry.get('postcode')
            locality = entry.get('locality')
            state = entry.get('state')
            latitude = entry.get('lat')
            longitude = entry.get('long')

            if not all([postcode_str, locality, state, latitude, longitude]):
                self.stdout.write(self.style.WARNING(f"Skipping entry due to missing data: {entry}"))
                skipped_count += 1
                continue

            try:
                postcode_obj, created = Postcode.objects.update_or_create(
                    postcode=postcode_str,
                    locality=locality,
                    state=state,
                    defaults={
                        'latitude': latitude,
                        'longitude': longitude,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing postcode {postcode_str} {locality}, {state}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS("\n--- Postcode Import Summary ---"))
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped_count}"))
        self.stdout.write(self.style.SUCCESS("-------------------------------"))
        self.stdout.write(self.style.SUCCESS("Postcode import complete."))
