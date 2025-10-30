import os
import random
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Count

from data_management.utils.analysis_utils.savings_benchmark import (
    generate_random_cart, 
    calculate_optimized_cost
)
from companies.models import Company, Store
from products.models import Price

class Command(BaseCommand):
    help = 'Runs a single, detailed savings benchmark and outputs the results to a file for debugging.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting single debug savings run..."))
        report_lines = [f"Debug Savings Run - {datetime.datetime.now()}\n"]

        PRODUCTS_PER_RUN = 100

        # --- Setup: Select stores for the run ---
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

        if len(selected_stores) < 2:
            self.stderr.write(self.style.ERROR("Not enough companies with viable stores to run."))
            return

        self.stdout.write(f"Running comparison across {len(selected_stores)} stores: {', '.join([s.store_name for s in selected_stores])}")

        # --- Step 1: Generate the Cart with Portfolios ---
        # We prefetch prices here to easily find the anchor's price later
        slots, anchor_products = generate_random_cart(selected_stores, PRODUCTS_PER_RUN)
        if not slots or not anchor_products:
            self.stderr.write(self.style.ERROR("Could not generate a valid cart for this run."))
            return
        
        self.stdout.write(f"Generated a cart with {len(slots)} items.")

        # --- Step 2: Run the Optimizer ---
        optimized_cost, shopping_plan, choice_vars = calculate_optimized_cost(slots, len(selected_stores))
        if optimized_cost is None:
            self.stderr.write(self.style.ERROR("Solver could not find an optimal solution."))
            return

        self.stdout.write(f"Solver found an optimal cost of ${optimized_cost:.2f}")

        # --- Step 3: Generate the Detailed Report ---
        for i, slot in enumerate(slots):
            anchor = anchor_products[i]
            
            # Find the cheapest price for the anchor product among the selected stores
            anchor_min_price = float('inf')
            for price_obj in Price.objects.filter(price_record__product=anchor):
                if price_obj.store in selected_stores and price_obj.price_record and price_obj.price_record.price < anchor_min_price:
                    anchor_min_price = price_obj.price_record.price

            report_lines.append(f"\n--- Cart Slot {i+1} ---")
            price_str = f"(Cheapest: ${anchor_min_price:.2f})" if anchor_min_price != float('inf') else "(Price not found)"
            report_lines.append(f"  Original Product: {anchor.brand} {anchor.name} {anchor.sizes} {price_str}")
            
            report_lines.append("\n  Considered Options:")
            
            chosen_option_index = -1
            for j, option in enumerate(slot):
                if choice_vars[(i, j)].varValue == 1:
                    chosen_option_index = j
                
                line = f"    - {option['brand']} {option['product_name']} {option.get('sizes', '')} @ {option['store_name']} for ${option['price']:.2f}"
                report_lines.append(line)

            report_lines.append("\n  Chosen Option:")
            if chosen_option_index != -1:
                chosen_option = slot[chosen_option_index]
                chosen_line = f"    -> {chosen_option['brand']} {chosen_option['product_name']} {chosen_option.get('sizes', '')} @ {chosen_option['store_name']} for ${chosen_option['price']:.2f}"
                report_lines.append(chosen_line)
            else:
                report_lines.append("    - No option chosen for this slot (error in solver). ")

        # --- Step 4: Write to File ---
        output_dir = os.path.join('data_management', 'data', 'analysis')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, 'debug_savings_run_output.txt')

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report_lines))
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully wrote debug report to: {file_path}"))
        except IOError as e:
            self.stderr.write(self.style.ERROR(f"Error writing to file: {e}"))
