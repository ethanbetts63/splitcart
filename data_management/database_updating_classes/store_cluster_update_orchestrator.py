import os
import json
from django.conf import settings
from companies.models import Company, Store, StoreGroup, StoreGroupMembership

class StoreClusterUpdateOrchestrator:
    """
    Orchestrates the database update process for store clusters.
    """

    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'store_clusters_inbox')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Store Cluster Update ---"))
        if not os.path.exists(self.inbox_path):
            self.command.stdout.write(self.command.style.WARNING('Store clusters inbox directory not found.'))
            return

        StoreGroupMembership.objects.all().delete()
        StoreGroup.objects.all().delete()

        for filename in os.listdir(self.inbox_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.inbox_path, filename)
            updater = StoreClusterUpdater(self.command, file_path)
            clusters_processed = updater.run()
            
            if clusters_processed is not None:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {clusters_processed} clusters from {filename}."))
                os.remove(file_path)
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SQL_FIELD("--- Store Cluster Update Complete ---"))

class StoreClusterUpdater:
    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'r') as f:
                clusters = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        clusters_processed = 0
        for cluster_data in clusters:
            try:
                company = Company.objects.get(name=cluster_data['company'])
                
                # Assuming cluster_data['stores'] contains a single store_id for initial groups
                store_id_for_anchor = cluster_data['stores'][0]
                anchor_store = Store.objects.get(id=store_id_for_anchor)
                
                group = StoreGroup.objects.create(company=company, anchor=anchor_store)
                
                for store_id in cluster_data['stores']:
                    try:
                        store = Store.objects.get(id=store_id)
                        StoreGroupMembership.objects.create(store=store, group=group)
                    except Store.DoesNotExist:
                        self.command.stderr.write(self.command.style.WARNING(f"  Store with ID {store_id} not found for cluster."))
                
                clusters_processed += 1
            except Company.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Company not found: {cluster_data['company']}"))
        
        return clusters_processed
