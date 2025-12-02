import json
from django.core.management.base import BaseCommand, CommandParser
import os

class Command(BaseCommand):
    help = 'Checks a JSONL file for missing "metadata" keys in each JSON object.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('jsonl_file_path', type=str, help='The path to the JSONL file to check.')

    def handle(self, *args, **options):
        jsonl_file_path = options['jsonl_file_path']

        if not os.path.exists(jsonl_file_path):
            self.stdout.write(self.style.ERROR(f"File not found at: {jsonl_file_path}"))
            return

        missing_metadata_count = 0
        total_lines = 0

        self.stdout.write(self.style.NOTICE(f"Checking file: {jsonl_file_path}"))

        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1
                try:
                    data = json.loads(line)
                    if 'metadata' not in data:
                        self.stdout.write(self.style.WARNING(f"  - Line {line_num}: Missing 'metadata' key."))
                        missing_metadata_count += 1
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f"  - Line {line_num}: Failed to parse as JSON."))
                    
        self.stdout.write(self.style.SUCCESS(f"\n--- Check Complete ---"))
        self.stdout.write(self.style.SUCCESS(f"Total lines processed: {total_lines}"))
        if missing_metadata_count > 0:
            self.stdout.write(self.style.ERROR(f"Lines missing 'metadata': {missing_metadata_count}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"All lines contain 'metadata' key."))
