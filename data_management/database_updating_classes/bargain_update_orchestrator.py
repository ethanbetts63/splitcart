import os
import json
import ijson
from django.conf import settings
from django.db import transaction
from products.models import Bargain

class BargainUpdateOrchestrator:
    """
    Orchestrates reading bargain data from files in the inbox and updating the database
    using a memory-efficient streaming approach.
    """

    def __init__(self, command):
        self.command = command
        self.inbox_dir = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox')

    def run(self):
        """
        The main public method that orchestrates the update process for all
        .json files found in the bargains_inbox.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Bargain Update (Streaming) ---"))
        
        try:
            json_files = [f.path for f in os.scandir(self.inbox_dir) if f.name.endswith('.json')]
        except FileNotFoundError:
            self.command.stdout.write(self.command.style.WARNING(f"  - Inbox directory not found: {self.inbox_dir}. Aborting."))
            return

        if not json_files:
            self.command.stdout.write(self.command.style.WARNING("  - No bargain files found in inbox. Nothing to do."))
            return
            
        self.command.stdout.write(f"  - Found {len(json_files)} bargain file(s) to process.")
        
        grand_total_created = 0

        for file_path in json_files:
            self.command.stdout.write(f"\n  --- Processing file: {os.path.basename(file_path)} ---")
            
            CHUNK_SIZE = 5000
            bargains_chunk = []
            total_in_file = 0

            try:
                self.command.stdout.write("    - Reading and processing bargains in chunks...")
                with open(file_path, 'rb') as f:
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
                            total_in_file += len(bargains_chunk)
                            self.command.stdout.write(f"\r      - Created {total_in_file:,} bargains from this file...", ending="")
                            bargains_chunk = []

                # Create any remaining bargains in the last chunk
                if bargains_chunk:
                    with transaction.atomic():
                        Bargain.objects.bulk_create(bargains_chunk, ignore_conflicts=True)
                    total_in_file += len(bargains_chunk)
                    self.command.stdout.write(f"\r      - Created {total_in_file:,} bargains from this file... Done.")

                self.command.stdout.write(f"\n    - Total new bargains from this file: {total_in_file:,}.")
                grand_total_created += total_in_file
                
                # Clean up the processed file
                os.remove(file_path)
                self.command.stdout.write(f"    - Successfully processed and removed source file.")

            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"\nAn error occurred while processing {os.path.basename(file_path)}: {e}"))
                self.command.stderr.write(self.command.style.WARNING("    - This file will be skipped and not deleted to allow for inspection."))
                continue # Move to the next file

        self.command.stdout.write(f"\n\n  - Grand total new bargains created across all files: {grand_total_created:,}.")
        self.command.stdout.write(self.command.style.SUCCESS("--- Bargain Update Complete ---"))
