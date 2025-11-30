import json
from django.conf import settings
from data_management.models.faq import FAQ

class FaqUpdateOrchestrator:
    def __init__(self, command):
        self.command = command

    def run(self):
        faq_file_path = settings.BASE_DIR / 'data_management' / 'data' / 'FAQ.jsonl'
        self.command.stdout.write(f"Importing FAQs from {faq_file_path}...")

        with open(faq_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    faq, created = FAQ.objects.update_or_create(
                        question=data['question'],
                        defaults={
                            'answer': data['answer'],
                            'pages': data['pages']
                        }
                    )
                    if created:
                        self.command.stdout.write(self.command.style.SUCCESS(f"Created FAQ: {faq.question}"))
                    else:
                        self.command.stdout.write(self.command.style.WARNING(f"Updated FAQ: {faq.question}"))
                except json.JSONDecodeError:
                    self.command.stderr.write(self.command.style.ERROR(f"Skipping invalid line: {line.strip()}"))
                except KeyError as e:
                    self.command.stderr.write(self.command.style.ERROR(f"Skipping line with missing key {e}: {line.strip()}"))

        self.command.stdout.write(self.command.style.SUCCESS("FAQ import complete."))
