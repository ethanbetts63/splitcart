import os
import json
from django.conf import settings
from django.db import transaction
from products.models import Bargain

class BargainUpdateOrchestrator:
    """
    Orchestrates reading bargain data from a file and updating the database.
    """

    def __init__(self, command):
        self.command = command
        # The generator places the file in the outbox; the orchestrator reads from there.
        self.source_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'bargains_outbox', 'new_bargains.json')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Bargain Update (from file) ---"))
        
        if not os.path.exists(self.source_path):
            self.command.stdout.write(self.command.style.WARNING(f"  - Source file not found: {self.source_path}. Aborting."))
            return

        # Read the bargain data from the JSON file
        self.command.stdout.write("  - Loading bargains from source file...")
        try:
            with open(self.source_path, 'r') as f:
                bargains_data = json.load(f)
            self.command.stdout.write(f"    - Found {len(bargains_data)} total bargains to process.")
        except (json.JSONDecodeError, IOError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"  - Error reading or parsing source file: {e}"))
            return

        if not bargains_data:
            self.command.stdout.write("  - No bargain data to process.")
            os.remove(self.source_path) # Clean up the empty file
            return

        try:
            with transaction.atomic():
                # Clear the table for a fresh import
                self.command.stdout.write("  - Deleting all existing bargain records...")
                count, _ = Bargain.objects.all().delete()
                self.command.stdout.write(f"    - Deleted {count} old records.")

                # Prepare Bargain objects in memory
                bargains_to_create = [
                    Bargain(
                        product_id=data['product_id'],
                        discount_percentage=data['discount_percentage'],
                        cheaper_store_id=data['cheaper_store_id'],
                        expensive_store_id=data['expensive_store_id']
                    )
                    for data in bargains_data
                ]

                # Bulk create the new objects
                self.command.stdout.write(f"  - Bulk creating {len(bargains_to_create)} new bargain records...")
                Bargain.objects.bulk_create(bargains_to_create, batch_size=1000)
                self.command.stdout.write("    - Bulk create complete.")

            # Clean up the processed file
            os.remove(self.source_path)
            self.command.stdout.write(f"  - Successfully processed and removed source file.")
            self.command.stdout.write(self.command.style.SUCCESS("--- Bargain Update Complete ---"))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during the bargain update transaction: {e}"))
            raise
