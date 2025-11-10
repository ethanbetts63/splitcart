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
                subs_data = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        cache = self._build_cache()
        
        subs_to_create = []
        subs_to_update = []
        
        total_subs = len(subs_data)
        self.command.stdout.write(f"  - Found {total_subs} substitutions to process.")

        for i, sub_data in enumerate(subs_data):
            self.command.stdout.write(f'\r    - Processing substitutions: {i+1}/{total_subs}', ending='')
            self._process_substitution(sub_data, cache, subs_to_create, subs_to_update)
        
        self.command.stdout.write('\n') # Newline after progress bar
        
        self._commit_changes(subs_to_create, subs_to_update)
        
        return len(subs_to_create) + len(subs_to_update)

    def _build_cache(self):
        self.command.stdout.write("  - Building cache of existing substitutions...")
        cache = {}
        for sub in ProductSubstitution.objects.all():
            key = tuple(sorted((sub.product_a_id, sub.product_b_id)))
            cache[key] = sub
        self.command.stdout.write(f"  - Cache built with {len(cache)} entries.")
        return cache

    def _process_substitution(self, sub_data, cache, subs_to_create, subs_to_update):
        try:
            product_a_id = sub_data['product_a']
            product_b_id = sub_data['product_b']
            key = tuple(sorted((product_a_id, product_b_id)))
            
            existing_sub = cache.get(key)

            if existing_sub:
                # It's an update, check if data has changed
                if (existing_sub.level != sub_data['level'] or
                    existing_sub.score != sub_data['score']):
                    
                    # Only add to the update list if it's a real, persisted object
                    if existing_sub.pk:
                        existing_sub.level = sub_data['level']
                        existing_sub.score = sub_data['score']
                        subs_to_update.append(existing_sub)
                    else:
                        # It's an in-memory object seen earlier in the file.
                        # Just update its values; it's already in subs_to_create.
                        existing_sub.level = sub_data['level']
                        existing_sub.score = sub_data['score']
            else:
                # It's a new substitution
                new_sub = ProductSubstitution(
                    product_a_id=product_a_id,
                    product_b_id=product_b_id,
                    level=sub_data['level'],
                    score=sub_data['score']
                )
                subs_to_create.append(new_sub)
                # Add to cache to handle duplicates within the same file
                cache[key] = new_sub
        except KeyError as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nMissing key {e} in substitution data: {sub_data}"))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nError processing substitution: {sub_data}. Error: {e}"))

    def _commit_changes(self, subs_to_create, subs_to_update):
        if not subs_to_create and not subs_to_update:
            self.command.stdout.write("  - No new or updated substitutions to commit.")
            return

        try:
            if subs_to_create:
                self.command.stdout.write(f"  - Bulk creating {len(subs_to_create)} new substitutions...")
                ProductSubstitution.objects.bulk_create(subs_to_create, batch_size=500)
            
            if subs_to_update:
                self.command.stdout.write(f"  - Bulk updating {len(subs_to_update)} existing substitutions...")
                ProductSubstitution.objects.bulk_update(subs_to_update, fields=['level', 'score'], batch_size=500)
            
            self.command.stdout.write(self.command.style.SUCCESS("  - Commit successful."))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nAn error occurred during bulk commit: {e}"))
