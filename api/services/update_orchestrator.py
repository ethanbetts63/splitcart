import os
import json
from products.models import Product, Price
from .product_resolver import ProductResolver
from .unit_of_work import UnitOfWork
from .variation_manager import VariationManager
from .translation_table_generator import TranslationTableGenerator

class UpdateOrchestrator:
    """
    The main entry point and controller of the entire database update process.
    """
    def __init__(self, command, inbox_path):
        self.command = command
        self.inbox_path = inbox_path
        self.unit_of_work = UnitOfWork(command)
        self.resolver = ProductResolver(command)
        self.variation_manager = VariationManager(command, self.unit_of_work)
        self.translator_generator = TranslationTableGenerator(command)

    def run(self):
        """
        Executes the full update process.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting OOP Refactored Product Update ---"))
        
        # Process all files in the inbox
        self._process_inbox_files()

        # Commit all collected changes to the database
        if self.unit_of_work.commit():
            # Only commit hotlist and remove files if DB commit was successful
            self.variation_manager.commit_hotlist()
            self._cleanup_processed_files()

        # Run post-update reconciliation
        self.variation_manager.reconcile_duplicates()

        # Generate the translation table as the final step
        self.translator_generator.generate()

        self.command.stdout.write(self.command.style.SUCCESS("--- Orchestrator finished ---"))

    def _process_inbox_files(self):
        self.processed_files = []
        for root, _, files in os.walk(self.inbox_path):
            for file in files:
                if file.endswith('.jsonl'):
                    file_path = os.path.join(root, file)
                    self.command.stdout.write(f"--- Processing file: {file} ---")
                    self._process_single_file(file_path)
                    self.processed_files.append(file_path)

    def _process_single_file(self, file_path):
        # This is a simplified data consolidation for demonstration.
        # The original logic for in-memory consolidation should be used here.
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # For this refactor, we'll process line-by-line without consolidation
                self._process_product(data)

    def _process_product(self, data):
        product_details = data
        price_history = data.get('price_history', [])
        company_name = data.get('company', '')

        if not price_history:
            return

        existing_product = self.resolver.find_match(product_details, price_history)

        if existing_product:
            # Handle existing product
            self.variation_manager.check_for_variation(product_details, existing_product, company_name)
            
            new_price = Price(
                product=existing_product,
                store_id=data.get('store_id'),
                price=price_history[0]['price'],
                date=price_history[0]['date']
            )
            self.unit_of_work.add_new_price(new_price)
        else:
            # Handle new product
            # NOTE: This does not handle store objects correctly yet. This is a simplification.
            new_product = Product(
                name=product_details.get('name', ''),
                brand=product_details.get('brand'),
                barcode=product_details.get('barcode'),
                store_product_id=product_details.get('store_product_id'),
                normalized_name_brand_size=product_details.get('normalized_name_brand_size')
            )
            self.unit_of_work.add_new_product(new_product)

            new_price = Price(
                product=new_product,
                store_id=data.get('store_id'),
                price=price_history[0]['price'],
                date=price_history[0]['date']
            )
            self.unit_of_work.add_new_price(new_price)

    def _cleanup_processed_files(self):
        self.command.stdout.write("--- Cleaning up processed inbox files ---")
        for file_path in self.processed_files:
            try:
                os.remove(file_path)
                self.command.stdout.write(f"  - Removed {os.path.basename(file_path)}")
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not remove file {file_path}: {e}'))