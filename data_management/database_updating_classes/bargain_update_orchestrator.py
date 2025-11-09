import os
import json
from django.conf import settings
from products.models import Bargain, Product, Price
from companies.models import Store

class BargainUpdateOrchestrator:
    """
    Orchestrates the database update process for bargains.
    """

    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'bargains_inbox')

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Bargain Update ---"))
        self.command.stdout.write(self.command.style.SUCCESS("  - Loading bargains from inbox..."))
        if not os.path.exists(self.inbox_path):
            self.command.stdout.write(self.command.style.WARNING('Bargains inbox directory not found.'))
            return

        Bargain.objects.all().delete()

        total_bargains_to_process = 0
        json_files = [f for f in os.listdir(self.inbox_path) if f.endswith('.json')]
        for filename in json_files:
            file_path = os.path.join(self.inbox_path, filename)
            try:
                with open(file_path, 'r') as f:
                    bargains = json.load(f)
                    total_bargains_to_process += len(bargains)
            except json.JSONDecodeError:
                self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {filename}, skipping for total count."))
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error reading {filename} for total count: {e}"))

        self.command.stdout.write(self.command.style.SUCCESS(f"  - Found {total_bargains_to_process} bargains to process."))

        bargains_processed_count = 0
        for filename in json_files:
            file_path = os.path.join(self.inbox_path, filename)
            updater = BargainUpdater(self.command, file_path)
            bargains_in_file = updater.run()
            
            if bargains_in_file is not None:
                bargains_processed_count += bargains_in_file
                self.command.stdout.write(self.command.style.SUCCESS(f"  - Processing bargains: {bargains_processed_count}/{total_bargains_to_process}"))
                os.remove(file_path)
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

        self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {bargains_processed_count}/{total_bargains_to_process} bargains."))
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Bargain Update Complete ---"))

class BargainUpdater:
    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'r') as f:
                bargains = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        bargains_processed = 0
        for bargain_data in bargains:
            try:
                product = Product.objects.get(id=bargain_data['product_id'])
                store = Store.objects.get(id=bargain_data['store_id'])
                cheapest_price = Price.objects.get(id=bargain_data['cheapest_price_id'])
                most_expensive_price = Price.objects.get(id=bargain_data['most_expensive_price_id'])

                primary_cat = product.category.primary_category if product.category else None
                Bargain.objects.create(
                    product=product,
                    store=store,
                    cheapest_price=cheapest_price,
                    most_expensive_price=most_expensive_price,
                    primary_category=primary_cat,
                )
                bargains_processed += 1
            except (Product.DoesNotExist, Store.DoesNotExist, Price.DoesNotExist) as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error processing bargain: {bargain_data}. Error: {e}"))
        
        return bargains_processed
