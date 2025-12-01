from django.utils import timezone
from datetime import timedelta
from companies.models import Company, Store
from products.models import Price

class StoreStatsGenerator:
    """
    A utility to report on the health of store pricing data.
    """
    def __init__(self, command):
        self.command = command

    def run(self):
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        companies = Company.objects.order_by('name')

        self.command.stdout.write(self.command.style.SUCCESS("Store Pricing Data Health Report"))
        self.command.stdout.write(self.command.style.SUCCESS("="*40))

        for company in companies:
            all_company_stores = Store.objects.filter(company=company)
            total_stores_count = all_company_stores.count()

            self.command.stdout.write(f"\nCompany: {self.command.style.HTTP_INFO(company.name)}")

            if total_stores_count == 0:
                self.command.stdout.write("  - No stores found.")
                continue

            anchor_ids = set(
                all_company_stores.select_related('group_membership__group')
                                  .values_list('group_membership__group__anchor_id', flat=True)
            )
            anchor_ids.discard(None)

            anchors_with_any_prices = set(
                Price.objects.filter(store_id__in=anchor_ids)
                             .values_list('store_id', flat=True)
                             .distinct()
            )

            anchors_with_fresh_prices = set(
                Price.objects.filter(store_id__in=anchor_ids, scraped_date__gte=seven_days_ago)
                             .values_list('store_id', flat=True)
                             .distinct()
            )

            stores_with_prices_count = all_company_stores.filter(
                group_membership__group__anchor_id__in=anchors_with_any_prices
            ).count()

            stores_with_fresh_prices_count = all_company_stores.filter(
                group_membership__group__anchor_id__in=anchors_with_fresh_prices
            ).count()
            
            stores_with_direct_prices_count = Price.objects.filter(
                store__company=company
            ).values('store_id').distinct().count()

            self.command.stdout.write(f"  - Total Stores: {total_stores_count}")
            self.command.stdout.write(f"  - Stores with Direct Price Data: {stores_with_direct_prices_count}")
            self.command.stdout.write(f"  - Stores with Price Data (via anchor): {stores_with_prices_count}")
            self.command.stdout.write(f"  - Stores with Fresh Price Data (last 7 days): {stores_with_fresh_prices_count}")
        
        self.command.stdout.write(self.command.style.SUCCESS("\n" + "="*40))
        self.command.stdout.write(self.command.style.SUCCESS("Report Complete."))
