import json
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Count
from companies.models import Store
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Analyzes the products for a given store PK to count field presence.'

    def add_arguments(self, parser):
        parser.add_argument('store_pk', type=int, help='The primary key of the store to analyze.')

    def handle(self, *args, **options):
        store_pk = options['store_pk']

        try:
            store = Store.objects.get(pk=store_pk)
        except Store.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Store with PK {store_pk} not found."))
            return

        # Get all unique product IDs that have a price entry for this store
        product_ids = Price.objects.filter(store=store).values_list('product_id', flat=True).distinct()
        products = Product.objects.filter(id__in=product_ids)
        total_products = products.count()

        if total_products == 0:
            self.stdout.write(self.style.WARNING(f"No products found for store: {store.store_name} (PK: {store_pk})"))
            return

        self.stdout.write(self.style.SUCCESS(f"\n--- Analysis for Store: {store.store_name} (PK: {store_pk}) ---"))
        self.stdout.write(f"Total products found: {total_products}\n")
        self.stdout.write(self.style.HTTP_INFO("Field presence analysis:"))

        field_counts = defaultdict(int)
        
        # Get all fields from the Product model
        product_fields = [f.name for f in Product._meta.get_fields() if not f.is_relation or f.one_to_one or (f.many_to_one and f.related_name)]

        for product in products.iterator():
            for field_name in product_fields:
                try:
                    value = getattr(product, field_name)
                    
                    # Check for non-empty/non-null values
                    if value is not None and value != '' and value != [] and value != {{}}:
                        # For related managers (like ManyToMany), we need to check existence
                        if hasattr(value, 'exists'):
                            if value.exists():
                                field_counts[field_name] += 1
                        else:
                            field_counts[field_name] += 1
                except AttributeError:
                    # This can happen for reverse relations that aren't direct fields
                    continue

        sorted_fields = sorted(product_fields)

        for field_name in sorted_fields:
            count = field_counts.get(field_name, 0)
            percentage = (count / total_products) * 100 if total_products > 0 else 0
            self.stdout.write(f"  - {field_name}: {count}/{total_products} ({percentage:.2f}%)")

        self.stdout.write(self.style.SUCCESS("\n--- Analysis Complete ---\n"))
