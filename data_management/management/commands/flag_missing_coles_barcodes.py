import os
import json
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Adds has_no_coles_barcode=True to products without a barcode in specified JSONL files.'

    def handle(self, *args, **options):
        target_directory = r'C:\Users\ethan\coding\splitcart\coles_products'

        if not os.path.isdir(target_directory):
            self.stderr.write(self.style.ERROR(f"Directory not found: {target_directory}"))
            return

        self.stdout.write(self.style.SUCCESS(f"--- Starting to process files in {target_directory} ---"))

        file_paths = [os.path.join(root, file) for root, _, files in os.walk(target_directory) for file in files if file.endswith('.jsonl')] 

        if not file_paths:
            self.stdout.write(self.style.WARNING("No .jsonl files found to process."))
            return

        total_files = len(file_paths)
        for i, file_path in enumerate(file_paths):
            self.stdout.write(f"Processing file {i+1}/{total_files}: {os.path.basename(file_path)}")
            temp_file_path = file_path + '.tmp'
            lines_modified = 0

            try:
                with open(file_path, 'r', encoding='utf-8') as infile, open(temp_file_path, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        try:
                            data = json.loads(line)
                            product_data = data.get('product')

                            # Check if barcode is missing or is an empty string
                            if product_data and not product_data.get('barcode'):
                                product_data['has_no_coles_barcode'] = True
                                lines_modified += 1
                            
                            outfile.write(json.dumps(data) + '\n')

                        except json.JSONDecodeError:
                            # If a line is not valid JSON, write it as is to not lose data.
                            outfile.write(line)
                
                # Replace the original file with the temporary one
                os.replace(temp_file_path, file_path)
                if lines_modified > 0:
                    self.stdout.write(self.style.SUCCESS(f"  -> Done. Modified {lines_modified} product lines."))
                else:
                    self.stdout.write("  -> Done. No modifications needed.")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  -> Error processing file {os.path.basename(file_path)}: {e}"))
                # Clean up temp file on error
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        self.stdout.write(self.style.SUCCESS("--- All files processed successfully. ---"))
