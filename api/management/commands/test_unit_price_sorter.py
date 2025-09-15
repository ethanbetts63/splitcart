import random
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
            # Find a store from each company that has at least 50 products
            viable_store = Store.objects.filter(company=company).annotate(num_prices=Count('prices')).filter(num_prices__gte=50).first()
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
            # Get a random product that is available in at least one of the selected stores
            product_ids_in_stores = Price.objects.filter(store__in=selected_stores).values_list('product_id', flat=True).distinct()
            if not product_ids_in_stores:
                self.stdout.write(self.style.ERROR("No products found in the selected stores."))
                return
            anchor_product = Product.objects.get(id=random.choice(list(product_ids_in_stores)))

        self.stdout.write(self.style.SUCCESS(f"Using anchor product: {anchor_product.brand} {anchor_product.name}"))

        # --- 3. Generate the list of product-price pairs ---
        # This mimics the logic from the savings benchmark
        substitute_products = get_substitution_group(anchor_product)
        self.stdout.write(f"Found {len(substitute_products)} substitutes (including anchor). Now finding prices...")

        product_price_pairs = []
        # Fetch all relevant prices in a single query for efficiency
        prices_in_stores = Price.objects.filter(
            product__in=substitute_products,
            store__in=selected_stores,
            is_active=True
        ).select_related('product', 'store')

        for price in prices_in_stores:
            product_price_pairs.append((price.product, price))

        if not product_price_pairs:
            self.stdout.write(self.style.ERROR('No product-price pairs were found for the selected substitutes. Aborting test.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(product_price_pairs)} product-price pairs to test.'))
        self.stdout.write('---')

        # --- 4. Instantiate the sorter and sort the products ---
        sorter = UnitPriceSorter()
        sorted_products = sorter.sort_by_unit_price(product_price_pairs)

        self.stdout.write(self.style.SUCCESS('--- Sorted Products (by Unit Price) ---'))
        for item in sorted_products:
            product = item['product']
            price = item['price']
            unit_price = item['unit_price']

            self.stdout.write(f"  Product: {product.brand} {product.name}")
            self.stdout.write(f"    Store: {price.store.store_name}")
            self.stdout.write(f"    Raw Sizes: {product.sizes}")
            self.stdout.write(f"    Absolute Price: ${price.price}")
            self.stdout.write(f"    Canonical Size: {item['canonical_size']}")
            self.stdout.write(self.style.SUCCESS(f"    Calculated Unit Price: ${unit_price:.4f} per base unit"))
            self.stdout.write('---')
