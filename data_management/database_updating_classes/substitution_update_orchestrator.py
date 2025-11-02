import os
import json
from django.conf import settings
from products.models import ProductSubstitution

class SubstitutionUpdateOrchestrator:
    """
    Orchestrates the database update process for substitutions.
    """

    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'substitutions_inbox')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Substitution Update ---"))
        if not os.path.exists(self.inbox_path):
            self.command.stdout.write(self.command.style.WARNING('Substitutions inbox directory not found.'))
            return

        for filename in os.listdir(self.inbox_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.inbox_path, filename)
            updater = SubstitutionUpdater(self.command, file_path)
            subs_processed = updater.run()
            
            if subs_processed is not None:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {subs_processed} substitutions from {filename}."))
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SQL_FIELD("--- Substitution Update Complete ---"))

class SubstitutionUpdater:
    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        self.command.stdout.write(f"  - Loading substitutions from {os.path.basename(self.file_path)}...")
        try:
            with open(self.file_path, 'r') as f:
                subs = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        subs_processed = 0
        total_subs = len(subs)
        self.command.stdout.write(f"  - Found {total_subs} substitutions to process.")
        for i, sub_data in enumerate(subs):
            try:
                ProductSubstitution.objects.update_or_create(
                    product_a_id=sub_data['product_a'],
                    product_b_id=sub_data['product_b'],
                    defaults={
                        'level': sub_data['level'],
                        'score': sub_data['score'],
                        'source': sub_data['source']
                    }
                )
                subs_processed += 1
                self.command.stdout.write(f'\r    - Processing substitutions: {subs_processed}/{total_subs}', ending='')
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"\nError processing substitution: {sub_data}. Error: {e}"))
        
        self.command.stdout.write('\n')
        return subs_processed
