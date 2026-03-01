from django.core.management.base import BaseCommand, CommandError
from companies.models import Store
from products.models import Price
from data_management.utils.price_comparer import PriceComparer

class Command(BaseCommand):
    help = 'Compares two stores by their product prices and reports the percentage of true overlap.'

    def add_arguments(self, parser):
        parser.add_argument('store_pk_a', type=int, help='Primary key of the first store.')
        parser.add_argument('store_pk_b', type=int, help='Primary key of the second store.')

    def handle(self, *args, **options):
        store_pk_a = options['store_pk_a']
        store_pk_b = options['store_pk_b']

        self.stdout.write(self.style.SUCCESS(f"--- Comparing Store {store_pk_a} and Store {store_pk_b} ---"))

        try:
            store_a = Store.objects.get(pk=store_pk_a)
            store_b = Store.objects.get(pk=store_pk_b)
        except Store.DoesNotExist:
            raise CommandError("One or both store PKs do not exist.")

        self.stdout.write(f"  Store A: {store_a.store_name} (ID: {store_a.id})")
        self.stdout.write(f"  Store B: {store_b.store_name} (ID: {store_b.id})")

        # Fetch prices for both stores
        prices_a = Price.objects.filter(store=store_a).values('product_id', 'price')
        prices_b = Price.objects.filter(store=store_b).values('product_id', 'price')

        price_map_a = {p['product_id']: p['price'] for p in prices_a}
        price_map_b = {p['product_id']: p['price'] for p in prices_b}

        if not price_map_a or not price_map_b:
            self.stdout.write(self.style.WARNING("One or both stores have no prices. Cannot compare."))
            self.stdout.write("True Overlap: 0.00%")
            return

        # Replicate PriceComparer's logic to get the percentage
        common_product_ids = set(price_map_a.keys()) & set(price_map_b.keys())

        if not common_product_ids:
            self.stdout.write(self.style.WARNING("No common products found between stores. Cannot compare."))
            self.stdout.write("True Overlap: 0.00%")
            return

        match_count = 0
        for product_id in common_product_ids:
            # Ensure comparison is between Decimal objects
            if price_map_a[product_id] == price_map_b[product_id]:
                match_count += 1

        true_overlap_percentage = (match_count / len(common_product_ids)) * 100 if common_product_ids else 0

        self.stdout.write(f"  Common Products: {len(common_product_ids)}")
        self.stdout.write(f"  Matching Prices for Common Products: {match_count}")
        self.stdout.write(self.style.SUCCESS(f"True Overlap: {true_overlap_percentage:.2f}%"))

        comparer = PriceComparer() # Instantiate to get the threshold
        if true_overlap_percentage / 100 >= comparer.overlap_threshold:
            self.stdout.write(self.style.SUCCESS(f"  (This is a MATCH based on {comparer.overlap_threshold*100:.0f}% threshold)"))
        else:
            self.stdout.write(self.style.WARNING(f"  (This is NOT a match based on {comparer.overlap_threshold*100:.0f}% threshold)"))
