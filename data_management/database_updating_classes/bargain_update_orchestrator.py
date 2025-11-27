import os
import json
import ijson
from django.conf import settings
from django.db import transaction
from products.models import Bargain

class BargainUpdateOrchestrator:
    """
    Orchestrates reading bargain data from a file and updating the database
    using a memory-efficient streaming approach.
    """

    def __init__(self, command):
        self.command = command
        # The uploader moves the file to the inbox for processing.
        self.source_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox', 'bargains.json')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Bargain Update (Streaming) ---"))
        
        if not os.path.exists(self.source_path):
            self.command.stdout.write(self.command.style.WARNING(f"  - Source file not found: {self.source_path}. Aborting."))
            return

        CHUNK_SIZE = 5000
        bargains_chunk = []
        total_created = 0

        try:
            self.command.stdout.write("  - Reading and processing bargains in chunks...")
            # Open file in binary mode for ijson
            with open(self.source_path, 'rb') as f:
                # Assuming the JSON file is a list of objects: [{...}, {...}]
                bargain_iterator = ijson.items(f, 'item')
                
                for data in bargain_iterator:
                    bargains_chunk.append(
                        Bargain(
                            product_id=data['product_id'],
                            discount_percentage=data['discount_percentage'],
                            cheaper_price_id=data['cheaper_price_id'],
                            expensive_price_id=data['expensive_price_id'],
                            cheaper_store_id=data['cheaper_store_id'],
                            expensive_store_id=data['expensive_store_id']
                        )
                    )

                    if len(bargains_chunk) >= CHUNK_SIZE:
                        with transaction.atomic():
                            Bargain.objects.bulk_create(bargains_chunk, ignore_conflicts=True)
                        total_created += len(bargains_chunk)
                        self.command.stdout.write(f"\r    - Created {total_created} bargains...", ending="")
                        bargains_chunk = []

            # Create any remaining bargains in the last chunk
            if bargains_chunk:
                with transaction.atomic():
                    Bargain.objects.bulk_create(bargains_chunk, ignore_conflicts=True)
                total_created += len(bargains_chunk)
                self.command.stdout.write(f"\r    - Created {total_created} bargains... Done.")

            self.command.stdout.write(f"\n  - Total new bargains created: {total_created}.")
            
            # Clean up the processed file
            os.remove(self.source_path)
            self.command.stdout.write(f"  - Successfully processed and removed source file.")
            self.command.stdout.write(self.command.style.SUCCESS("--- Bargain Update Complete ---"))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nAn error occurred during the bargain update transaction: {e}"))
            # Don't remove the source file if an error occurs, so it can be inspected/retried
            raise
