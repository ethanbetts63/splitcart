import os
import json
from django.conf import settings
from companies.models.category_link import CategoryLink

class CategoryLinkUpdateOrchestrator:
    """
    Orchestrates the database update process for category links.
    """

    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'category_links_inbox')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Category Link Update ---"))
        if not os.path.exists(self.inbox_path):
            self.command.stdout.write(self.command.style.WARNING('Category links inbox directory not found.'))
            return

        for filename in os.listdir(self.inbox_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.inbox_path, filename)
            updater = CategoryLinkUpdater(self.command, file_path)
            links_processed = updater.run()
            
            if links_processed is not None:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {links_processed} links from {filename}."))
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SQL_FIELD("--- Category Link Update Complete ---"))

class CategoryLinkUpdater:
    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'r') as f:
                links = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        links_processed = 0
        for link_data in links:
            try:
                # Assuming the JSON structure matches the model fields
                CategoryLink.objects.update_or_create(
                    category_a_id=link_data['category_a'],
                    category_b_id=link_data['category_b'],
                    defaults={
                        'link_type': link_data['link_type'],
                        'similarity_score': link_data.get('similarity_score')
                    }
                )
                links_processed += 1
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error processing link: {link_data}. Error: {e}"))
        
        return links_processed
