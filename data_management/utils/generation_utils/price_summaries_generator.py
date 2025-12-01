import time
from django.db import transaction
from django.db.models import Count
from products.models import Product, ProductPriceSummary

class PriceSummariesGenerator:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Starting product price summary update..."))
        start_time = time.time()

        products_to_summarize = Product.objects.annotate(price_count=Count('prices')).filter(price_count__gte=2)
        product_ids = list(products_to_summarize.values_list('id', flat=True))
        total_products_to_process = len(product_ids)
        
        self.command.stdout.write(f"Found {total_products_to_process} products with 2 or more prices to summarize.")

        self.command.stdout.write("Deleting old summaries in chunks of 5000...")
        chunk_size = 5000
        for i in range(0, total_products_to_process, chunk_size):
            chunk_ids = product_ids[i:i + chunk_size]
            deleted_count, _ = ProductPriceSummary.objects.filter(product_id__in=chunk_ids).delete()
            if deleted_count > 0:
                progress = min(i + chunk_size, total_products_to_process)
                self.command.stdout.write(f"  - Chunk {i // chunk_size + 1}: Deleted {deleted_count} old summaries. ({progress}/{total_products_to_process})")

        self.command.stdout.write("\nCalculating and creating new summaries in chunks of 5000...")
        summaries_to_create = []
        total_processed = 0
        total_created = 0

        for product in products_to_summarize.iterator():
            total_processed += 1
            prices = product.prices.select_related('store__company').all()

            if len(prices) < 2:
                continue

            price_values = [p.price for p in prices]
            min_price = min(price_values)
            max_price = max(price_values)

            if min_price == max_price:
                continue

            company_ids = set()
            iga_store_count = 0
            for p in prices:
                company_ids.add(p.store.company.id)
                if p.store.company.name.lower() == 'iga':
                    iga_store_count += 1
            
            company_count = len(company_ids)

            if company_count < 2 and iga_store_count < 2:
                continue

            best_possible_discount = 0
            if max_price > 0:
                best_possible_discount = int(((max_price - min_price) / max_price) * 100)

            if not (5 <= best_possible_discount <= 70):
                continue

            summaries_to_create.append(
                ProductPriceSummary(
                    product=product, min_price=min_price, max_price=max_price,
                    company_count=company_count, iga_store_count=iga_store_count,
                    best_possible_discount=best_possible_discount
                )
            )

            if len(summaries_to_create) >= chunk_size:
                with transaction.atomic():
                    ProductPriceSummary.objects.bulk_create(summaries_to_create, batch_size=500)
                
                self.command.stdout.write(f"  - Created {len(summaries_to_create)} summaries. Progress: {total_processed}/{total_products_to_process} products checked.")
                total_created += len(summaries_to_create)
                summaries_to_create = []

        if summaries_to_create:
            with transaction.atomic():
                ProductPriceSummary.objects.bulk_create(summaries_to_create, batch_size=500)
            self.command.stdout.write(f"  - Created final {len(summaries_to_create)} summaries. Progress: {total_processed}/{total_products_to_process} products checked.")
            total_created += len(summaries_to_create)

        end_time = time.time()
        duration = end_time - start_time
        
        self.command.stdout.write(self.command.style.SUCCESS(f"\nSuccessfully created a total of {total_created} product price summaries."))
        self.command.stdout.write(self.command.style.SUCCESS(f"Operation took {duration:.2f} seconds."))
