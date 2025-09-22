import random
import re
from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Product, Price
from companies.models import Store, Company
from api.utils.substitution_utils.unit_price_sorter import UnitPriceSorter
from api.utils.analysis_utils.savings_benchmark import get_substitution_group

class Command(BaseCommand):
    help = 'Tests the UnitPriceSorter utility with a programmatically generated list of products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Attempting to generate a product list for sorting..."))

        # --- 1. Setup: Select stores for the test ---
        selected_stores = []
        all_companies = Company.objects.all()
        for company in all_companies:
            viable_store = Store.objects.filter(company=company).annotate(num_prices=Count('price')).filter(num_prices__gte=50).first()
            if viable_store:
                selected_stores.append(viable_store)

        if len(selected_stores) < 2:
            self.stdout.write(self.style.ERROR("Not enough companies with viable stores to run the test."))
            return

        self.stdout.write(f"Selected stores for test: {', '.join([s.store_name for s in selected_stores])}")

        # --- 2. Find a suitable anchor product ---
        anchor_product = Product.objects.filter(name__icontains='tortellini').first()
        if not anchor_product:
            self.stdout.write(self.style.WARNING("Could not find a 'tortellini' product, picking a random one."))
            product_ids_in_stores = Price.objects.filter(store__in=selected_stores).values_list('price_record__product_id', flat=True).distinct()
            if not product_ids_in_stores:
                self.stdout.write(self.style.ERROR("No products found in the selected stores."))
                return
            anchor_product = Product.objects.get(id=random.choice(list(product_ids_in_stores)))

        self.stdout.write(self.style.SUCCESS(f"Using anchor product: {anchor_product.brand} {anchor_product.name}"))

        # --- 3. Generate the list of product-price pairs ---
        substitute_products = get_substitution_group(anchor_product)
        self.stdout.write(f"Found {len(substitute_products)} substitutes (including anchor). Now finding prices...")

        product_price_pairs = []
        prices_in_stores = Price.objects.filter(
            price_record__product__in=substitute_products,
            store__in=selected_stores,
            is_active=True
        ).select_related('price_record__product', 'store', 'price_record')

        for price in prices_in_stores:
            product_price_pairs.append((price.price_record.product, price))

        if not product_price_pairs:
            self.stdout.write(self.style.ERROR('No product-price pairs were found for the selected substitutes. Aborting test.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(product_price_pairs)} product-price pairs to test.'))
        self.stdout.write('---')

        # --- 4. DEBUGGING: Inspect the raw data before sorting ---
        self.stdout.write(self.style.HTTP_INFO('--- Inspecting Raw Data Before Sorting ---'))
        for product, price in product_price_pairs:
            if not price.price_record:
                self.stdout.write(self.style.WARNING(f"  Product {product.name} has a Price entry with no PriceRecord. Skipping."))
                continue
            self.stdout.write(f"  Product: {product.name}")
            self.stdout.write(f"    Store: {price.store.store_name}")
            u_price = price.price_record.unit_price
            u_measure = price.price_record.unit_of_measure
            self.stdout.write(f"    Unit Price from DB: {u_price}")
            self.stdout.write(f"    Unit Measure from DB: {u_measure}")
            if u_price is None or not u_measure:
                self.stdout.write(self.style.WARNING('    -> REASON: Missing data in database.'))
            else:
                # Simulate the regex match from the sorter
                uom_pattern = re.compile(r'(\d*\.?\d+)?\s*([a-zA-Z]+)')
                match = uom_pattern.match(u_measure.lower())
                if not match:
                    self.stdout.write(self.style.WARNING(f'    -> REASON: unit_of_measure "{u_measure}" failed to parse.'))
            self.stdout.write('---')


        # --- 5. Instantiate the sorter and sort the products ---
        sorter = UnitPriceSorter()
        sorted_products = sorter.sort_by_unit_price(product_price_pairs)

        self.stdout.write(self.style.SUCCESS('--- Sorted Products (by Normalized Unit Price) ---'))
        current_base_unit = None
        for item in sorted_products:
            product = item['product']
            price = item['price']
            normalized_unit_price = item['normalized_unit_price']
            base_unit = item['base_unit']

            if base_unit != current_base_unit:
                self.stdout.write(self.style.HTTP_INFO(f"\n--- Sorting by Price per '{base_unit.upper()}' ---"))
                current_base_unit = base_unit
            
            if not price.price_record: continue

            self.stdout.write(f"  Product: {product.brand} {product.name}")
            self.stdout.write(f"    Store: {price.store.store_name}")
            self.stdout.write(f"    Absolute Price: ${price.price_record.price}")
            self.stdout.write(f"    Original Unit Price: ${price.price_record.unit_price} / {price.price_record.unit_of_measure}")
            self.stdout.write(self.style.SUCCESS(f"    NORMALIZED Unit Price: ${normalized_unit_price:.2f} / per {base_unit}"))
            self.stdout.write('---')
