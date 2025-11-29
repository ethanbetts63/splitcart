from django.core.management.base import BaseCommand
from products.models import Product
from companies.models import Company
from data_management.models import BargainStats
from collections import defaultdict
import itertools

class Command(BaseCommand):
    help = 'Calculates and stores bargain statistics between companies.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting bargain stats calculation...")

        products = Product.objects.prefetch_related('prices__store__company').all()
        
        # {('Coles', 'Woolworths'): {'Coles': 10, 'Woolworths': 5}}
        pair_wins = defaultdict(lambda: defaultdict(int))
        
        # {('Coles', 'Woolworths'): 15}
        pair_total_bargains = defaultdict(int)

        self.stdout.write(f"Processing {len(products)} products...")
        
        for i, product in enumerate(products):
            if i > 0 and i % 1000 == 0:
                self.stdout.write(f"  - Processed {i} products...")

            prices = product.prices.all()
            if len(prices) < 2:
                continue

            # Find the min price and the companies offering it
            min_price = None
            cheapest_companies = []
            for p in prices:
                if min_price is None or p.price < min_price:
                    min_price = p.price
                    cheapest_companies = {p.store.company.name}
                elif p.price == min_price:
                    cheapest_companies.add(p.store.company.name)
            
            # Find the max price among other companies
            max_price_other_company = None
            most_expensive_companies = set()
            for p in prices:
                if p.store.company.name not in cheapest_companies:
                    if max_price_other_company is None or p.price > max_price_other_company:
                        max_price_other_company = p.price
                        most_expensive_companies = {p.store.company.name}
                    elif p.price == max_price_other_company:
                        most_expensive_companies.add(p.store.company.name)

            # A bargain exists if there's a clear cheaper and more expensive price
            if min_price is not None and max_price_other_company is not None and max_price_other_company > min_price:
                # We have a bargain. Attribute it to all pairs of one cheapest company vs one most expensive company.
                for cheap_co in cheapest_companies:
                    for expensive_co in most_expensive_companies:
                        # Sort company names to create a canonical pair key
                        pair_key = tuple(sorted((cheap_co, expensive_co)))
                        
                        pair_wins[pair_key][cheap_co] += 1
                        pair_total_bargains[pair_key] += 1
        
        self.stdout.write("Aggregated bargain data. Now calculating percentages...")
        
        final_stats = []
        all_company_names = [c.name for c in Company.objects.all()]
        
        for company_a_name, company_b_name in itertools.combinations(all_company_names, 2):
            pair_key = tuple(sorted((company_a_name, company_b_name)))
            
            total_bargains_for_pair = pair_total_bargains.get(pair_key, 0)
            if total_bargains_for_pair == 0:
                continue

            wins_a = pair_wins.get(pair_key, {}).get(company_a_name, 0)
            wins_b = pair_wins.get(pair_key, {}).get(company_b_name, 0)
            
            percent_a = round((wins_a / total_bargains_for_pair) * 100) if total_bargains_for_pair > 0 else 0
            percent_b = round((wins_b / total_bargains_for_pair) * 100) if total_bargains_for_pair > 0 else 0
            
            # The remainder to 100 is for 'same price', which is not applicable in this bargain context,
            # but we'll calculate it to fulfill the chart component's data structure.
            # It should mostly be 0.
            percent_same = 100 - percent_a - percent_b

            final_stats.append({
                'company_a_name': company_a_name,
                'company_b_name': company_b_name,
                'cheaper_at_a_percentage': percent_a,
                'cheaper_at_b_percentage': percent_b,
                'same_price_percentage': percent_same,
                'overlap_count': total_bargains_for_pair
            })

        BargainStats.objects.update_or_create(
            key='company_bargain_comparison',
            defaults={'data': final_stats}
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully calculated and stored bargain stats for {len(final_stats)} company pairs."))
