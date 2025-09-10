from django.core.management.base import BaseCommand
from django.db.models import Count
import random
import json

from companies.models import Company, Store
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Generates a test shopping cart with substitutes for the optimization algorithm.'

    def handle(self, *args, **options):
        self.stderr.write("Generating test shopping cart...")

        # 1. Select the store with the most products from each company
        selected_stores = []
        companies = Company.objects.all()
        for company in companies:
            best_store = Store.objects.filter(company=company).annotate(
                num_products=Count('prices')
            ).order_by('-num_products').first()
            
            if best_store and best_store.num_products > 0:
                selected_stores.append(best_store)
        
        if not selected_stores:
            self.stdout.write(self.style.ERROR("No stores with products found in the database."))
            return

        self.stderr.write(f"Selected stores: {[s.store_name for s in selected_stores]}")

        # 2. Select 100 random products from the selected stores
        product_ids_in_stores = Price.objects.filter(store__in=selected_stores).values_list('product_id', flat=True).distinct()
        
        if len(product_ids_in_stores) < 50:
            self.stdout.write(self.style.ERROR(f"Not enough unique products ({len(product_ids_in_stores)}) in selected stores to form a list of 50."))
            return

        random_product_ids = random.sample(list(product_ids_in_stores), 50)
        anchor_products = Product.objects.filter(id__in=random_product_ids)

        self.stderr.write(f"Selected {anchor_products.count()} anchor products.")

        # 3. For each anchor, find a random substitute and build the slots
        all_slots = []
        for anchor_product in anchor_products:
            products_in_slot = {anchor_product}

            # Find all substitutes by matching the normalized_name
            substitutes = Product.objects.filter(
                normalized_name=anchor_product.normalized_name
            ).exclude(id=anchor_product.id)

            if substitutes.exists():
                for substitute_product in substitutes:
                    products_in_slot.add(substitute_product)

            # 4. Build the slot with all available options in the selected stores
            current_slot = []
            for product in products_in_slot:
                # Find all prices for this product in our list of selected stores
                prices_in_stores = Price.objects.filter(product=product, store__in=selected_stores)
                for price_obj in prices_in_stores:
                    option = {
                        "product_id": product.id,
                        "product_name": product.name,
                        "brand": product.brand,
                        "store_id": price_obj.store.id,
                        "store_name": price_obj.store.store_name,
                        "price": float(price_obj.price),
                        "unit_price": float(price_obj.unit_price) if price_obj.unit_price is not None else None,
                        "unit_of_measurement": price_obj.unit_of_measure,
                    }
                    current_slot.append(option)
            
            if current_slot:
                all_slots.append(current_slot)

        self.stderr.write(f"Generated {len(all_slots)} slots for the test cart.")

        # 5. Print the final data structure
        self.stdout.write(json.dumps(all_slots, indent=2))