from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from companies.models import Company, Store
from products.models import Price

class Command(BaseCommand):
    """
    A management command to report on the health of store pricing data.

    This command provides a summary for each company, detailing:
    - The total number of stores.
    - The number of stores with prices directly attached (typically anchor stores or ungrouped stores).
    - The number of stores associated with an anchor that has any price data.
    - The number of stores associated with an anchor that has fresh price data
      (scraped within the last 7 days).

    This helps in assessing data coverage and freshness across the platform.
    """
    help = 'Displays statistics about stores and their price data freshness for each company.'

    def handle(self, *args, **options):
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        companies = Company.objects.order_by('name')

        self.stdout.write(self.style.SUCCESS("Store Pricing Data Health Report"))
        self.stdout.write(self.style.SUCCESS("="*40))

        for company in companies:
            all_company_stores = Store.objects.filter(company=company)
            total_stores_count = all_company_stores.count()

            self.stdout.write(f"\nCompany: {self.style.HTTP_INFO(company.name)}")

            if total_stores_count == 0:
                self.stdout.write("  - No stores found.")
                continue

            # Get a set of unique anchor store IDs for all stores in the company.
            # This is the definitive list of stores that *should* have price data.
            anchor_ids = set(
                all_company_stores.select_related('group_membership__group')
                                  .values_list('group_membership__group__anchor_id', flat=True)
            )
            anchor_ids.discard(None)  # Remove None if any stores are not in a group

            # Find which of these anchor stores have ANY price data.
            anchors_with_any_prices = set(
                Price.objects.filter(store_id__in=anchor_ids)
                             .values_list('store_id', flat=True)
                             .distinct()
            )

            # Find which of these anchor stores have FRESH price data.
            anchors_with_fresh_prices = set(
                Price.objects.filter(store_id__in=anchor_ids, scraped_date__gte=seven_days_ago)
                             .values_list('store_id', flat=True)
                             .distinct()
            )

            # Count how many stores in the company point to an anchor with any prices.
            stores_with_prices_count = all_company_stores.filter(
                group_membership__group__anchor_id__in=anchors_with_any_prices
            ).count()

            # Count how many stores in the company point to an anchor with fresh prices.
            stores_with_fresh_prices_count = all_company_stores.filter(
                group_membership__group__anchor_id__in=anchors_with_fresh_prices
            ).count()
            
            # Count stores that have their own price data.
            # This includes anchor stores and ungrouped stores with recent scrapes.
            stores_with_direct_prices_count = Price.objects.filter(
                store__company=company
            ).values('store_id').distinct().count()

            self.stdout.write(f"  - Total Stores: {total_stores_count}")
            self.stdout.write(f"  - Stores with Direct Price Data: {stores_with_direct_prices_count}")
            self.stdout.write(f"  - Stores with Price Data (via anchor): {stores_with_prices_count}")
            self.stdout.write(f"  - Stores with Fresh Price Data (last 7 days): {stores_with_fresh_prices_count}")
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*40))
        self.stdout.write(self.style.SUCCESS("Report Complete."))