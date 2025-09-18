from django.core.management.base import BaseCommand
from api.utils.archive.database_archiver import DatabaseArchiver

class Command(BaseCommand):
    help = 'Archives all database models to individual JSON files.'

    def handle(self, *args, **options):
        archiver = DatabaseArchiver()
        # Pass the command instance to the archiver so it can write output
        archiver.command = self
        archiver.run()
