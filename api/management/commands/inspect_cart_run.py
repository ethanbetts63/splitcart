from django.core.management.base import BaseCommand
import random
from django.db.models import Count
from companies.models import Company, Store
from api.utils.analysis_utils.savings_benchmark import generate_random_cart, calculate_optimized_cost, calculate_baseline_cost

class Command(BaseCommand):
    help = 'Inspects a single optimized shopping cart run to show the original list and the final shopping plan.'

    def handle(self, *args, **options):
        PRODUCTS_PER_RUN = 20

        self.stdout.write("--- Setting up a single shopping run for inspection ---")

        # 1. Select one viable store from each company.
        selected_stores = []
        all_companies = Company.objects.all()

        for company in all_companies:
            viable_stores_for_company = Store.objects.filter(
                company=company
            ).annotate(
                num_prices=Count('prices')
            ).filter(
                num_prices__gte=PRODUCTS_PER_RUN
            )

            if viable_stores_for_company.exists():
                random_store = random.choice(list(viable_stores_for_company))
                selected_stores.append(random_store)

        if not selected_stores:
            self.stdout.write(self.style.ERROR("Could not find any viable stores from any company."))
            return

        # The number of stores for the solver is now dynamic.
        MAX_STORES_FOR_SOLVER = len(selected_stores)

        store_names = [s.store_name for s in selected_stores]
        self.stdout.write(self.style.SUCCESS(f"Selected Stores: {', '.join(store_names)}"))

        # 2. Generate cart
        slots, anchor_products = generate_random_cart(selected_stores, PRODUCTS_PER_RUN)
        
        if not slots or not anchor_products:
            self.stdout.write(self.style.ERROR("Failed to generate a valid cart for this run."))
            return

        # 3. Print original list
        self.stdout.write(self.style.HTTP_INFO("\n--- Original Shopping List ---"))
        anchor_products_sorted = sorted(anchor_products, key=lambda p: f"{p.brand or ''} {p.name or ''}")
        for i, product in enumerate(anchor_products_sorted):
            brand_safe = (product.brand.name if product.brand else '').encode('ascii', 'ignore').decode('ascii')
            name_safe = (product.name or '').encode('ascii', 'ignore').decode('ascii')
            self.stdout.write(f"{i+1}. {brand_safe} {name_safe}")

        # 4. Solve for the optimal plan
        optimized_cost, shopping_plan = calculate_optimized_cost(slots, MAX_STORES_FOR_SOLVER)

        if optimized_cost is None:
            self.stdout.write(self.style.ERROR("Solver failed to find an optimal solution."))
            return

        # 5. Calculate baseline and savings
        baseline_cost = calculate_baseline_cost(slots, selected_stores)
        savings = 0
        if baseline_cost > 0 and baseline_cost > optimized_cost:
            savings = ((baseline_cost - optimized_cost) / baseline_cost) * 100

        # 6. Print the plan
        self.stdout.write(self.style.HTTP_INFO(f"\n--- Optimal Shopping Plan ---"))
        self.stdout.write(f"Baseline Cost:  ${baseline_cost:.2f}")
        self.stdout.write(f"Optimized Cost: ${optimized_cost:.2f}")
        self.stdout.write(self.style.SUCCESS(f"Savings: {savings:.2f}%"))

        for store, items in shopping_plan.items():
            if items:
                store_name_safe = (store or '').encode('ascii', 'ignore').decode('ascii')
                self.stdout.write(self.style.SUCCESS(f"\nGo to {store_name_safe}:"))
                # Sort items for consistent output
                sorted_items = sorted(items, key=lambda x: x['product'])
                store_subtotal = 0
                for item_details in sorted_items:
                    product_name_safe = (item_details['product'] or '').encode('ascii', 'ignore').decode('ascii')
                    self.stdout.write(f"  - Buy {product_name_safe}: ${item_details['price']:.2f}")
                    store_subtotal += item_details['price']
                self.stdout.write(self.style.HTTP_REDIRECT(f"  Subtotal for {store}: ${store_subtotal:.2f}"))
        
        self.stdout.write(self.style.SUCCESS("\n--- Inspection Complete ---"))
