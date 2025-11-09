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

from companies.models.primary_category import PrimaryCategory

class BargainUpdater:
    def __init__(self, command, file_path):
        self.command = command
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'r') as f:
                bargains_data = json.load(f)
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Invalid JSON in {self.file_path}"))
            return None

        if not bargains_data:
            return 0

        # 1. Pre-fetch all required data
        product_ids = {b['product_id'] for b in bargains_data}
        store_ids = {b['store_id'] for b in bargains_data}
        price_ids = {b['cheapest_price_id'] for b in bargains_data} | {b['most_expensive_price_id'] for b in bargains_data}

        products = Product.objects.filter(id__in=product_ids).prefetch_related('category__primary_category')
        stores = Store.objects.filter(id__in=store_ids)
        prices = Price.objects.filter(id__in=price_ids)

        products_map = {p.id: p for p in products}
        stores_map = {s.id: s for s in stores}
        prices_map = {p.id: p for p in prices}

        # 2. Prepare Bargain objects and M2M relationships in memory
        bargains_to_create = []
        bargain_cats_map = {}
        
        total_in_file = len(bargains_data)
        for i, bargain_data in enumerate(bargains_data):
            product = products_map.get(bargain_data['product_id'])
            store = stores_map.get(bargain_data['store_id'])
            cheapest_price = prices_map.get(bargain_data['cheapest_price_id'])
            most_expensive_price = prices_map.get(bargain_data['most_expensive_price_id'])

            if not all([product, store, cheapest_price, most_expensive_price]):
                self.command.stderr.write(self.command.style.ERROR(f"Skipping bargain due to missing data: {bargain_data}"))
                continue

            bargains_to_create.append(Bargain(
                product=product,
                store=store,
                cheapest_price=cheapest_price,
                most_expensive_price=most_expensive_price,
            ))

            primary_cats_to_add = set()
            if product.category.exists():
                for cat in product.category.all():
                    if cat.primary_category:
                        primary_cats_to_add.add(cat.primary_category)
            
            if primary_cats_to_add:
                bargain_cats_map[(product.id, store.id)] = primary_cats_to_add
            
            if (i + 1) % 100 == 0 or (i + 1) == total_in_file:
                self.command.stdout.write(f"\r        - Preparing bargains: {i + 1}/{total_in_file}...", ending="")

        self.command.stdout.write("") # Newline after prep

        # 3. Bulk create Bargain objects
        self.command.stdout.write("  - Bulk creating bargains...")
        Bargain.objects.bulk_create(bargains_to_create, batch_size=500)

        # 4. Efficiently set M2M relationships
        self.command.stdout.write("  - Setting primary category relationships...")
        newly_created_bargains = Bargain.objects.filter(product_id__in=product_ids)
        
        BargainPrimaryCategory = Bargain.primary_categories.through
        m2m_relations_to_create = []

        for bargain in newly_created_bargains:
            cats_to_add = bargain_cats_map.get((bargain.product_id, bargain.store_id))
            if cats_to_add:
                for cat in cats_to_add:
                    m2m_relations_to_create.append(
                        BargainPrimaryCategory(bargain_id=bargain.id, primarycategory_id=cat.id)
                    )
        
        BargainPrimaryCategory.objects.bulk_create(m2m_relations_to_create, batch_size=500, ignore_conflicts=True)

        return len(bargains_to_create)
