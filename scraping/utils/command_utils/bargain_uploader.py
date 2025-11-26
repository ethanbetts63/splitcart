import os
import shutil
from django.conf import settings

class BargainUploader:
    """
    Handles the "upload" of the generated bargains file by moving it
    from the outbox to the inbox for processing.
    """
    def __init__(self, command, dev=False):
        self.command = command
        # The 'dev' flag is not used but kept for interface consistency.
        self.dev = dev
        self.source_file = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'bargains_outbox', 'bargains.json')
        self.inbox_dir = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox')
        self.destination_file = os.path.join(self.inbox_dir, 'bargains.json')

    def run(self):
        """
        Executes the file moving operation.
        """
        if not os.path.exists(self.source_file):
            self.command.stdout.write(self.command.style.WARNING(f"  - No bargain file found at {self.source_file}. Nothing to upload."))
            return

        try:
            # Ensure the inbox directory exists
            os.makedirs(self.inbox_dir, exist_ok=True)
            
            # Move the file
            shutil.move(self.source_file, self.destination_file)
            self.command.stdout.write(self.command.style.SUCCESS(f"  - Successfully moved bargain file to inbox for processing."))
            
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"  - An error occurred while moving the bargain file: {e}"))
            raise
