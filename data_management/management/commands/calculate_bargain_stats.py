from django.core.management.base import BaseCommand
from products.models import Product
from companies.models import Company
from data_management.models import BargainStats
import itertools

class Command(BaseCommand):
    help = 'Calculates and stores product price comparison statistics between companies.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting price comparison stats calculation...")

        all_companies = list(Company.objects.all())
        final_stats = []

        for company_a, company_b in itertools.combinations(all_companies, 2):
            self.stdout.write(f"  - Processing {company_a.name} vs {company_b.name}...")

            # Find products that have a price from BOTH companies. This is the overlap.
            products_in_a = Product.objects.filter(prices__store__company=company_a)
            overlap_products_qs = products_in_a.filter(prices__store__company=company_b).distinct()

            overlap_count = overlap_products_qs.count()
            if overlap_count == 0:
                self.stdout.write(f"    No overlapping products found. Skipping.")
                continue
            
            self.stdout.write(f"    Found {overlap_count} overlapping products.")

            # Initialize counters for this pair
            wins_a = 0
            wins_b = 0
            same_price = 0

            # Iterate efficiently through only the overlapping products
            for i, product in enumerate(overlap_products_qs.prefetch_related('prices__store__company').iterator(chunk_size=2000)):
                if i > 0 and i % 1000 == 0:
                    self.stdout.write(f"      ... processed {i} of {overlap_count} products.")

                # For a given product, find the minimum price from each company in the pair
                prices_a = [p.price for p in product.prices.all() if p.store.company_id == company_a.id]
                prices_b = [p.price for p in product.prices.all() if p.store.company_id == company_b.id]

                # This condition should theoretically not be met because of the initial query, but it's a safeguard.
                if not prices_a or not prices_b:
                    continue
                
                min_price_a = min(prices_a)
                min_price_b = min(prices_b)

                if min_price_a < min_price_b:
                    wins_a += 1
                elif min_price_b < min_price_a:
                    wins_b += 1
                else:
                    same_price += 1
            
            self.stdout.write(f"    Calculation complete. Wins for {company_a.name}: {wins_a}, Wins for {company_b.name}: {wins_b}, Same price: {same_price}")

            # Calculate percentages
            percent_a = round((wins_a / overlap_count) * 100) if overlap_count > 0 else 0
            percent_b = round((wins_b / overlap_count) * 100) if overlap_count > 0 else 0
            # Derive the 'same' percentage last to ensure the total is always 100 due to rounding
            percent_same = 100 - percent_a - percent_b

            final_stats.append({
                'company_a_name': company_a.name,
                'company_b_name': company_b.name,
                'cheaper_at_a_percentage': percent_a,
                'cheaper_at_b_percentage': percent_b,
                'same_price_percentage': percent_same,
                'overlap_count': overlap_count
            })

        BargainStats.objects.update_or_create(
            key='company_bargain_comparison',
            defaults={'data': final_stats}
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully calculated and stored price comparison stats for {len(final_stats)} company pairs."))

