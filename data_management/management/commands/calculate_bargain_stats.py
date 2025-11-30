from django.core.management.base import BaseCommand
from products.models import Product
from companies.models import Company
from data_management.models import BargainStats
from collections import defaultdict
import itertools

class Command(BaseCommand):
    help = 'Calculates and stores product price comparison statistics between companies.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting price comparison stats calculation...")

        product_count = Product.objects.count()
        products_iterator = Product.objects.prefetch_related('prices__store__company').iterator(chunk_size=5000)
        
        # This dictionary will store the aggregate stats in memory.
        # Key: (sorted_company_name_a, sorted_company_name_b)
        # Value: defaultdict with keys like 'overlap_count', 'same_price', and company names for wins.
        stats = defaultdict(lambda: defaultdict(int))

        self.stdout.write(f"Processing {product_count} products...")
        
        for i, product in enumerate(products_iterator):
            if i > 0 and i % 10000 == 0:
                self.stdout.write(f"  - Processed {i} of {product_count} products...")

            # 1. For the current product, group its prices by company.
            prices_by_company = defaultdict(list)
            for p in product.prices.all():
                prices_by_company[p.store.company.name].append(p.price)

            # Find the minimum price for each company for this product.
            min_prices = {name: min(price_list) for name, price_list in prices_by_company.items()}

            # 2. If more than one company sells this product, update stats for all relevant pairs.
            if len(min_prices) > 1:
                for company_a_name, company_b_name in itertools.combinations(min_prices.keys(), 2):
                    # Ensure a consistent key for the pair.
                    pair_key = tuple(sorted((company_a_name, company_b_name)))
                    
                    # This product is part of the overlap for this pair.
                    stats[pair_key]['overlap_count'] += 1
                    
                    price_a = min_prices[company_a_name]
                    price_b = min_prices[company_b_name]

                    if price_a < price_b:
                        stats[pair_key][company_a_name] += 1
                    elif price_b < price_a:
                        stats[pair_key][company_b_name] += 1
                    else:
                        stats[pair_key]['same_price'] += 1

        self.stdout.write("Aggregated all product data. Now finalizing statistics...")

        # 3. Format the aggregated data for storage.
        final_stats = []
        all_company_names = [c.name for c in Company.objects.all()]
        
        for company_a_name, company_b_name in itertools.combinations(all_company_names, 2):
            pair_key = tuple(sorted((company_a_name, company_b_name)))
            pair_stats = stats.get(pair_key)

            if not pair_stats or pair_stats['overlap_count'] == 0:
                continue
            
            overlap_count = pair_stats['overlap_count']
            # Use the pair_key to correctly reference wins for company 'a' and 'b' from the loop
            wins_for_a_in_pair = pair_stats.get(pair_key[0], 0)
            wins_for_b_in_pair = pair_stats.get(pair_key[1], 0)

            # Ensure we assign the stats to the correct original company name from the outer loop
            if pair_key[0] == company_a_name:
                wins_a = wins_for_a_in_pair
                wins_b = wins_for_b_in_pair
            else:
                wins_a = wins_for_b_in_pair
                wins_b = wins_for_a_in_pair

            percent_a = round((wins_a / overlap_count) * 100) if overlap_count > 0 else 0
            percent_b = round((wins_b / overlap_count) * 100) if overlap_count > 0 else 0
            percent_same = 100 - percent_a - percent_b
            
            final_stats.append({
                'company_a_name': company_a_name,
                'company_b_name': company_b_name,
                'cheaper_at_a_percentage': percent_a,
                'cheaper_at_b_percentage': percent_b,
                'same_price_percentage': percent_same,
                'overlap_count': overlap_count
            })

        # 4. Save the final stats to the database.
        BargainStats.objects.update_or_create(
            key='company_bargain_comparison',
            defaults={'data': final_stats}
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully calculated and stored price comparison stats for {len(final_stats)} company pairs."))

