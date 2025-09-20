from django.core.management.base import BaseCommand
from api.utils.analysis_utils.geographic_clustering import create_geographic_clusters

class Command(BaseCommand):
    help = 'Automatically groups stores into geographic clusters using DBSCAN.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting geographic clustering process..."))
        
        success = create_geographic_clusters()
        
        if success:
            self.stdout.write(self.style.SUCCESS("\nGeographic clustering process completed successfully."))
        else:
            self.stdout.write(self.style.ERROR("Geographic clustering process failed."))

