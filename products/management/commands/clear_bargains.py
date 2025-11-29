from django.core.management.base import BaseCommand
from django.db import connection
from products.models import Bargain

class Command(BaseCommand):
    help = 'Deletes all Bargain objects from the database to prepare for a schema migration.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- Attempting to delete all Bargain objects... ---'))
        
        table_name = Bargain._meta.db_table
        
        try:
            with connection.cursor() as cursor:
                # Use TRUNCATE for most databases for performance, but SQLite does not support it.
                if connection.vendor == 'sqlite':
                    self.stdout.write(self.style.NOTICE(f'Using "DELETE FROM" for SQLite backend...'))
                    cursor.execute(f"DELETE FROM {table_name};")
                else:
                    self.stdout.write(self.style.NOTICE(f'Using "TRUNCATE TABLE" for {connection.vendor} backend...'))
                    cursor.execute(f"TRUNCATE TABLE {table_name};")

            self.stdout.write(self.style.SUCCESS(f'Successfully cleared all objects from the "{table_name}" table.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.WARNING('This may be because the Bargain model and database table are out of sync or due to database permissions.'))
            self.stdout.write(self.style.WARNING('If this command fails, you may need to manually drop or truncate the `products_bargain` table in your database before running `migrate`.'))
