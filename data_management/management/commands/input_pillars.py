import json
from django.core.management.base import BaseCommand
from django.db import transaction
from companies.models import PillarPage, PrimaryCategory
from django.conf import settings

class Command(BaseCommand):
    help = 'Imports Pillar Pages from a JSONL file into the database.'

    def handle(self, *args, **options):
        pillar_pages_file_path = settings.BASE_DIR / 'data_management' / 'data' / 'pillar_contents' / 'pillar_pages.jsonl'
        self.stdout.write(f"Importing Pillar Pages from {pillar_pages_file_path}...")

        with open(pillar_pages_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    slug = data['slug']
                    primary_category_slugs = data.get('primary_category_slugs', [])

                    with transaction.atomic():
                        pillar_page, created = PillarPage.objects.update_or_create(
                            slug=slug,
                            defaults={
                                'name': data['name'],
                                'hero_title': data['hero_title'],
                                'introduction_paragraph': data['introduction_paragraph'],
                            }
                        )

                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created Pillar Page: {pillar_page.name}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"Updated Pillar Page: {pillar_page.name}"))

                        # Handle Many-to-Many relationship for primary_categories
                        if primary_category_slugs:
                            primary_categories = []
                            for cat_slug in primary_category_slugs:
                                try:
                                    category = PrimaryCategory.objects.get(slug=cat_slug)
                                    primary_categories.append(category)
                                except PrimaryCategory.DoesNotExist:
                                    self.stderr.write(self.style.ERROR(f"PrimaryCategory with slug '{cat_slug}' does not exist. Skipping for Pillar Page '{slug}'."))
                            pillar_page.primary_categories.set(primary_categories)
                            self.stdout.write(f"  - Linked {len(primary_categories)} primary categories.")

                except json.JSONDecodeError:
                    self.stderr.write(self.style.ERROR(f"Skipping invalid line: {line.strip()}"))
                except KeyError as e:
                    self.stderr.write(self.style.ERROR(f"Skipping line with missing key {e}: {line.strip()}"))

        self.stdout.write(self.style.SUCCESS("Pillar Page import complete."))
