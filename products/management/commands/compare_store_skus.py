import json
from django.core.management.base import BaseCommand
from companies.models import Store
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Compares the Coles SKUs for a store in the DB against the SKUs in a JSONL file.'

    def add_arguments(self, parser):
        parser.add_argument('store_pk', type=int, help='The primary key of the store to analyze in the database.')
        parser.add_argument('file_path', type=str, help='The path to the .jsonl file to compare.')

    def handle(self, *args, **options):
        store_pk = options['store_pk']
        file_path = options['file_path']

        self.stdout.write(self.style.SUCCESS(f"--- Comparing SKUs for Store PK {store_pk} and File {file_path} ---"))

        try:
            # --- Step 1: Get SKUs from the Database ---
            self.stdout.write(f"1. Fetching SKUs from database for Store PK {store_pk}...")
            store = Store.objects.get(pk=store_pk)
            product_ids = Price.objects.filter(store=store).values_list('product_id', flat=True).distinct()
            products_in_db = Product.objects.filter(id__in=product_ids, company_skus__has_key='coles')
            
            db_skus = set()
            for product in products_in_db.iterator():
                coles_skus = product.company_skus.get('coles', [])
                if not isinstance(coles_skus, list):
                    coles_skus = [coles_skus]
                for sku in coles_skus:
                    try:
                        db_skus.add(int(sku))
                    except (ValueError, TypeError):
                        continue
            self.stdout.write(f"   - Found {len(db_skus)} unique Coles SKUs in the database for this store.")

            # --- Step 2: Get SKUs from the File ---
            self.stdout.write(f"2. Fetching SKUs from file: {file_path}...")
            file_skus = set()
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        sku = data.get('product', {}).get('sku')
                        if sku:
                            file_skus.add(int(sku))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
            self.stdout.write(f"   - Found {len(file_skus)} unique SKUs in the file.")

            # --- Step 3: Compare the Sets & Print Report ---
            self.stdout.write(self.style.HTTP_INFO("\n--- Comparison Report ---"))
            
            if not db_skus and not file_skus:
                self.stdout.write("Both database and file contain no SKUs to compare.")
                return

            intersection = db_skus.intersection(file_skus)
            db_only = db_skus - file_skus
            file_only = file_skus - db_skus

            self.stdout.write(f"  - Overlapping SKUs (in both DB and file): {len(intersection)}")
            self.stdout.write(f"  - SKUs only in Database: {len(db_only)}")
            self.stdout.write(f"  - SKUs only in File: {len(file_only)}")

            if db_only:
                self.stdout.write(f"    - Sample of SKUs only in DB: {sorted(list(db_only))[:10]}")
            if file_only:
                self.stdout.write(f"    - Sample of SKUs only in File: {sorted(list(file_only))[:10]}")

        except Store.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Store with PK {store_pk} not found."))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Comparison Complete ---"))
