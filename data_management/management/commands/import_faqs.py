import json
from django.core.management.base import BaseCommand
from data_management.models.faq import FAQ
from django.conf import settings

class Command(BaseCommand):
    help = 'Imports FAQs from a JSONL file into the database.'

    def handle(self, *args, **options):
        faq_file_path = settings.BASE_DIR / 'data_management' / 'data' / 'FAQ.jsonl'
        self.stdout.write(f"Importing FAQs from {faq_file_path}...")

        with open(faq_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    faq, created = FAQ.objects.update_or_create(
                        question=data['question'],
                        page=data['page'],
                        defaults={'answer': data['answer']}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created FAQ: {faq.question}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Updated FAQ: {faq.question}"))
                except json.JSONDecodeError:
                    self.stderr.write(self.style.ERROR(f"Skipping invalid line: {line.strip()}"))
                except KeyError as e:
                    self.stderr.write(self.style.ERROR(f"Skipping line with missing key {e}: {line.strip()}"))

        self.stdout.write(self.style.SUCCESS("FAQ import complete."))
