from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

from companies.models import Store
from products.models import Price


class Command(BaseCommand):
    """
    Analyzes the price data for non-anchor stores to diagnose potential
    issues with the price deletion logic in the group maintenance process.
    """
    help = "Verifies the freshness of prices for non-anchor stores."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Analyzing Non-Anchor Store Pricing ---"))

        # A non-anchor store is one that belongs to a group but is not the anchor of that group.
        non_anchor_stores = Store.objects.filter(
            group_membership__isnull=False
        ).exclude(
            id=F('group_membership__group__anchor_id')
        )

        total_non_anchor_stores = non_anchor_stores.count()
        self.stdout.write(f"Found {total_non_anchor_stores} total non-anchor stores to analyze.")

        if total_non_anchor_stores == 0:
            self.stdout.write(self.style.SUCCESS("No non-anchor stores found. System is clean."))
            return

        seven_days_ago = timezone.now().date() - timedelta(days=7)
        stores_with_prices = 0
        stores_with_only_stale_prices = 0
        stores_with_any_fresh_prices = 0

        # Create a list to store details of stores with fresh prices for later output
        fresh_price_stores_details = []

        for store in non_anchor_stores.iterator():
            prices = Price.objects.filter(store=store)
            if not prices.exists():
                continue

            stores_with_prices += 1

            if prices.filter(scraped_date__gte=seven_days_ago).exists():
                stores_with_any_fresh_prices += 1
                price_count = prices.count()
                fresh_price_stores_details.append(
                    f"  - Store '{store.store_name}' (ID: {store.id}, Company: {store.company.name}) has {price_count} prices, including at least one FRESH price."
                )
            else:
                stores_with_only_stale_prices += 1

        # --- Reporting ---
        self.stdout.write(self.style.SUCCESS("\n--- Analysis Complete ---"))
        self.stdout.write(f"\nTotal Non-Anchor Stores Analyzed: {total_non_anchor_stores}")
        self.stdout.write(f"Non-Anchor Stores with Any Price Data: {stores_with_prices}")

        self.stdout.write(self.style.NOTICE(f"  - Stores with ONLY stale prices (> 7 days old): {stores_with_only_stale_prices}"))
        self.stdout.write(self.style.WARNING(f"  - Stores with at least one FRESH price (<= 7 days old): {stores_with_any_fresh_prices}"))

        if stores_with_any_fresh_prices > 0:
            self.stdout.write(self.style.WARNING("\nDetailed list of non-anchor stores with FRESH prices:"))
            for detail in fresh_price_stores_details:
                self.stdout.write(detail)

            self.stdout.write(self.style.ERROR("\n[Conclusion]"))
            self.stdout.write("Your hypothesis is incorrect. The presence of FRESH prices on non-anchor stores strongly supports the 'Health Check Cache' theory.")
            self.stdout.write("This means stores are scraped, but the cleanup is skipped because they were marked as 'healthy' within the last 7 days, allowing fresh prices to persist.")
        
        elif stores_with_only_stale_prices > 0:
            self.stdout.write(self.style.SUCCESS("\n[Conclusion]"))
            self.stdout.write("Your hypothesis is correct. The presence of ONLY STALE prices on non-anchor stores supports the 'Stale Member Prices' theory.")
            self.stdout.write("This indicates that as a member's prices age past 7 days, the health checker ignores the store, and the prices are never deleted.")
        
        else:
            self.stdout.write(self.style.SUCCESS("\n[Conclusion]"))
            self.stdout.write("No non-anchor stores have price data. The cleanup process is working perfectly.")
