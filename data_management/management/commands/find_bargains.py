from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from products.models import Product, Bargain
from django.db import transaction
from decimal import Decimal, InvalidOperation # Import InvalidOperation

class Command(BaseCommand):
    help = 'Finds products that are significantly cheaper in one store compared to others and populates the Bargain model.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to find bargains...")
        bargain_count = 0

        self.stdout.write("Clearing old bargain data...")
        Bargain.objects.all().delete()

        product_queryset = Product.objects.all().order_by('id')
        paginator = Paginator(product_queryset, 200)  # Process 200 products at a time

        for page_number in paginator.page_range:
            self.stdout.write(f"Processing page {page_number}/{paginator.num_pages}...")
            page = paginator.page(page_number)

            try:
                # Prefetch for the products on the current page and evaluate the queryset
                products_on_page = list(Product.objects.filter(
                    id__in=[p.id for p in page.object_list]
                ).prefetch_related('price_records__price_entries__store'))
            except InvalidOperation as e:
                self.stdout.write(self.style.WARNING(f"Skipping page {page_number} due to invalid decimal data in a price record. Error: {e}"))
                continue # Skip this page

            with transaction.atomic():  # Atomic transaction for each chunk
                for product in products_on_page:
                    price_entries = []
                    for record in product.price_records.all():
                        price_entries.extend(list(record.price_entries.all()))

                    if len(price_entries) < 2:
                        continue

                    min_price_entry = min(price_entries, key=lambda p: p.price_record.price)
                    max_price_entry = max(price_entries, key=lambda p: p.price_record.price)

                    if min_price_entry.store == max_price_entry.store:
                        continue

                    min_price = min_price_entry.price_record.price
                    max_price = max_price_entry.price_record.price

                    if min_price > 0 and max_price > (min_price * Decimal('1.5')):
                        percentage_difference = ((max_price - min_price) / min_price) * Decimal('100')

                        Bargain.objects.create(
                            product=product,
                            store=min_price_entry.store,
                            cheapest_price=min_price_entry,
                            most_expensive_price=max_price_entry,
                            percentage_difference=float(percentage_difference)
                        )
                        bargain_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully found and created {bargain_count} bargains."))
