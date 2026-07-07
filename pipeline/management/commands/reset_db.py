import shutil

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

# Full pipeline sequence (local = run on dev machine, server = run on PythonAnywhere)
# Preserved here for reference until this command is extended to handle data loading.
#
# python manage.py upload --products --dev                 # local
# python manage.py update --products                       # server
# python manage.py update --prefixes                       # server
# python manage.py generate --cat-links --dev              # local
# python manage.py upload --cat-links --dev                # local
# python manage.py update --cat-links                      # server
# python manage.py upload --products --dev                 # local
# python manage.py update --products                       # server
# python manage.py generate --subs --dev                   # local
# python manage.py upload --subs --dev                     # local
# python manage.py update --subs                           # server
# python manage.py generate --primary-cats                 # server
# python manage.py generate --bargain-stats                # server
# python manage.py generate --pillars                      # server
# python manage.py generate --price-comps                  # server
# python manage.py update --faqs                           # server
# python manage.py generate --price-summaries              # server
# python manage.py analyze --report company_heatmap        # server
# python manage.py analyze --report subs                   # server
# python manage.py analyze --report savings                # server
# python manage.py analyze --report category_product_counts --strict  # server
# python manage.py generate --map --dev                    # local


class Command(BaseCommand):
    help = "Drop all tables, rebuild schema, and restore from private product archive"

    def handle(self, *args, **options):
        self.stdout.write("Pulling private archive...")
        call_command("archive", pull=True)

        self.stdout.write("Dropping all tables...")
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            tables = connection.introspection.table_names(cursor)
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                self.stdout.write(f"  Dropped: {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        self.stdout.write("Clearing __pycache__...")
        for cache_dir in settings.BASE_DIR.rglob("__pycache__"):
            if "venv" in cache_dir.parts:
                continue
            shutil.rmtree(cache_dir)

        self.stdout.write("\nRunning migrate...")
        call_command("migrate")

        self._reset_scraping_data()

        self.stdout.write("\nRestoring products from private archive...")
        call_command("update", products=True, archive=True)

        self.stdout.write("\nRegenerating derived data...")
        call_command("generate", primary_cats=True)
        call_command("generate", pillars=True)
        call_command("generate", bargain_stats=True)
        call_command("generate", price_comps=True)
        call_command("generate", price_summaries=True)
        call_command("generate", default_companies=True)

        self.stdout.write(self.style.SUCCESS("\nDatabase reset complete."))

    def _reset_scraping_data(self):
        scraping_data = settings.BASE_DIR / 'scraping' / 'data'

        # Reset translation tables to empty dicts so the scraper doesn't crash
        for name in (
            'brand_translation_table.json',
            'product_normalized_name_brand_size_translation_table.json',
        ):
            path = scraping_data / name
            path.write_text('{}', encoding='utf-8')
            self.stdout.write(f"  Reset: scraping/data/{name}")

        # Remove stale etag and progress files
        for pattern in ('*.etag', '*.progress'):
            for f in scraping_data.glob(pattern):
                f.unlink()
                self.stdout.write(f"  Removed: scraping/data/{f.name}")
