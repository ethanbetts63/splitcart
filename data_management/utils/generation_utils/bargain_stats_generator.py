from products.models import Product
from companies.models import Company
from data_management.models import BargainStats
from collections import defaultdict
import itertools

class BargainStatsGenerator:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write("Starting price comparison stats calculation...")

        product_count = Product.objects.count()
        products_iterator = Product.objects.prefetch_related('prices__store__company').iterator(chunk_size=5000)
        
        stats = defaultdict(lambda: defaultdict(int))

        self.command.stdout.write(f"Processing {product_count} products...")
        
        for i, product in enumerate(products_iterator):
            if i > 0 and i % 10000 == 0:
                self.command.stdout.write(f"  - Processed {i} of {product_count} products...")

            prices_by_company = defaultdict(list)
            for p in product.prices.all():
                prices_by_company[p.store.company.name].append(p.price)

            # Use average for IGA, min for others.
            comparison_prices = {}
            for name, price_list in prices_by_company.items():
                if name == 'Iga':
                    comparison_prices[name] = sum(price_list) / len(price_list)
                else:
                    comparison_prices[name] = min(price_list)

            if len(comparison_prices) > 1:
                for company_a_name, company_b_name in itertools.combinations(comparison_prices.keys(), 2):
                    pair_key = tuple(sorted((company_a_name, company_b_name)))
                    
                    stats[pair_key]['overlap_count'] += 1
                    
                    price_a = comparison_prices[company_a_name]
                    price_b = comparison_prices[company_b_name]

                    if price_a < price_b:
                        stats[pair_key][company_a_name] += 1
                    elif price_b < price_a:
                        stats[pair_key][company_b_name] += 1
                    else:
                        stats[pair_key]['same_price'] += 1

        self.command.stdout.write("Aggregated all product data. Now finalizing statistics...")

        final_stats = []
        all_company_names = [c.name for c in Company.objects.all()]
        
        for company_a_name, company_b_name in itertools.combinations(all_company_names, 2):
            pair_key = tuple(sorted((company_a_name, company_b_name)))
            pair_stats = stats.get(pair_key)

            if not pair_stats or pair_stats['overlap_count'] == 0:
                continue
            
            overlap_count = pair_stats['overlap_count']
            wins_for_a_in_pair = pair_stats.get(pair_key[0], 0)
            wins_for_b_in_pair = pair_stats.get(pair_key[1], 0)

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

        BargainStats.objects.update_or_create(
            key='company_bargain_comparison',
            defaults={'data': final_stats}
        )

        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully calculated and stored price comparison stats for {len(final_stats)} company pairs."))