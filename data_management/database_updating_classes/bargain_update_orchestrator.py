import os
import json
from django.conf import settings
from products.models import Bargain, Product, PriceRecord
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
        if not os.path.exists(self.inbox_path):
            self.command.stdout.write(self.command.style.WARNING('Bargains inbox directory not found.'))
            return

        Bargain.objects.all().delete()

        for filename in os.listdir(self.inbox_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.inbox_path, filename)
            updater = BargainUpdater(self.command, file_path)
            bargains_processed = updater.run()
            
            if bargains_processed is not None:
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully processed {bargains_processed} bargains from {filename}."))
                os.remove(file_path)
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  Failed to process {filename}."))

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
                cheapest_price_record = PriceRecord.objects.get(id=bargain_data['cheapest_price_record_id'])
                most_expensive_price_record = PriceRecord.objects.get(id=bargain_data['most_expensive_price_record_id'])

                Bargain.objects.create(
                    product=product,
                    store=store,
                    cheapest_price=cheapest_price_record.price_entries.first(),
                    most_expensive_price=most_expensive_price_record.price_entries.first(),
                    percentage_difference=bargain_data['percentage_difference']
                )
                bargains_processed += 1
            except (Product.DoesNotExist, Store.DoesNotExist, PriceRecord.DoesNotExist) as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error processing bargain: {bargain_data}. Error: {e}"))
        
        return bargains_processed
