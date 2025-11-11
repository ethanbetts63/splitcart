import json
from collections import defaultdict
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Analyzes a .jsonl product file to count products and field presence.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the .jsonl file to analyze.')

    def handle(self, *args, **options):
        file_path = options['file_path']
        total_products = 0
        field_counts = defaultdict(int)
        all_fields = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        product_data = data.get('product')
                        if product_data:
                            total_products += 1
                            all_fields.update(product_data.keys())
                            for key, value in product_data.items():
                                # Count if the key exists and the value is not None or empty
                                if value is not None and value != '':
                                    field_counts[key] += 1
                    except json.JSONDecodeError:
                        self.stdout.write(self.style.WARNING(f"Skipping a line due to JSON decode error."))
                        continue
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        if total_products == 0:
            self.stdout.write(self.style.WARNING("No products found in the file."))
            return

        self.stdout.write(self.style.SUCCESS(f"\n--- Analysis for {file_path} ---"))
        self.stdout.write(f"Total products found: {total_products}\n")

        self.stdout.write(self.style.HTTP_INFO("Field presence analysis:"))
        sorted_fields = sorted(list(all_fields))
        
        for field in sorted_fields:
            count = field_counts.get(field, 0)
            percentage = (count / total_products) * 100 if total_products > 0 else 0
            self.stdout.write(f"  - {field}: {count}/{total_products} ({percentage:.2f}%)")
            
        self.stdout.write(self.style.SUCCESS("\n--- Analysis Complete ---\\n"))
