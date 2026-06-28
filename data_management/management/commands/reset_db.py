import shutil

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

APPS_WITH_MIGRATIONS = [
    "companies",
    "data_management",
    "products",
    "users",
]

# Full pipeline sequence (local = run on dev machine, server = run on PythonAnywhere)
# Preserved here for reference until this command is extended to handle data loading.
#
# python manage.py update --archive                        # server
# python manage.py generate --store-groups                 # server
# python manage.py upload --product --dev                  # local
# python manage.py update --products                       # server
# python manage.py update --prefixes                       # server
# python manage.py generate --cat-links --dev              # local
# python manage.py upload --cat-links --dev                # local
# python manage.py update --cat-links                      # server
# python manage.py upload --product --dev                  # local
# python manage.py update --products                       # server
# python manage.py generate --subs --dev                   # local
# python manage.py upload --subs --dev                     # local
# python manage.py update --subs                           # server
# python manage.py generate --primary-cats                 # server
# python manage.py generate --bargain-stats                # server
# python manage.py generate --pillars                      # server
# python manage.py generate --price-comps                  # server
# python manage.py update --faqs                           # server
# python manage.py generate --store-stats                  # server
# python manage.py generate --price-summaries              # server
# python manage.py generate --default-stores               # server
# python manage.py analyze --report company_heatmap        # server
# python manage.py analyze --report subs                   # server
# python manage.py analyze --report savings                # server
# python manage.py analyze --report category_product_counts --strict  # server
# python manage.py generate --map --dev                    # local


class Command(BaseCommand):
    help = "Drop all tables, wipe migrations, rebuild schema"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR

        self.stdout.write("Dropping all tables...")
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            tables = connection.introspection.table_names(cursor)
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                self.stdout.write(f"  Dropped: {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        self.stdout.write("Deleting migration files...")
        for app in APPS_WITH_MIGRATIONS:
            migrations_dir = base_dir / app / "migrations"
            for f in migrations_dir.glob("*.py"):
                if f.name != "__init__.py":
                    f.unlink()
                    self.stdout.write(f"  Deleted: {app}/migrations/{f.name}")

        self.stdout.write("Clearing __pycache__...")
        for cache_dir in base_dir.rglob("__pycache__"):
            if "venv" in cache_dir.parts:
                continue
            shutil.rmtree(cache_dir)

        self.stdout.write("\nRunning makemigrations...")
        call_command("makemigrations")

        self.stdout.write("\nRunning migrate...")
        call_command("migrate")

        self.stdout.write(self.style.SUCCESS("\nDatabase reset complete."))
