from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from products.models import Price, Product
from companies.models import Store, Company, StoreGroup

class Command(BaseCommand):
    help = 'Runs a series of diagnostic checks on the pricing data to identify inconsistencies and potential issues.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Starting Pricing Data Health Report ---'))

        # === Section 1: Integrity Checks ===
        self.stdout.write(self.style.HTTP_INFO('\n[Section 1: Integrity Checks]'))

        # Check for orphaned prices (where product or store FK is invalid)
        # This is difficult to do efficiently with the ORM if FK constraints are not enforced.
        # We will assume FK constraints are working and focus on other diagnostics for now.
        # A simple count can verify this assumption.
        total_prices = Price.objects.count()
        prices_with_valid_relations = Price.objects.filter(product__isnull=False, store__isnull=False).count()
        orphaned_prices = total_prices - prices_with_valid_relations
        self.stdout.write(f'- Orphaned Prices (pointing to non-existent products or stores): {orphaned_prices}')

        products_without_prices = Product.objects.annotate(price_count=Count('prices')).filter(price_count=0).count()
        self.stdout.write(f'- Products without any prices: {products_without_prices}')

        # === Section 2: Duplication Analysis ===
        self.stdout.write(self.style.HTTP_INFO('\n[Section 2: Duplication Analysis]'))

        # Find hard duplicates (same product and store)
        duplicate_groups = Price.objects.values('product_id', 'store_id').annotate(count=Count('id')).filter(count__gt=1)
        duplicate_group_count = duplicate_groups.count()
        
        if duplicate_group_count > 0:
            self.stdout.write(self.style.ERROR(f'- Found {duplicate_group_count} Product/Store pairs with >1 Price record (Major Issue!)'))
            self.stdout.write('  - Top 5 examples:')
            for group in duplicate_groups.order_by('-count')[:5]:
                self.stdout.write(f'    - Product ID {group['product_id']}, Store ID {group['store_id']}: {group['count']} price records')
        else:
            self.stdout.write(self.style.SUCCESS('- No duplicate Product/Store price records found.'))

        # Price Count Distribution
        self.stdout.write("\n- Price Count Distribution per Product:")
        product_price_counts = Product.objects.annotate(price_count=Count('prices')).values_list('price_count', flat=True)
        
        counts_list = list(product_price_counts)
        total_products_with_prices = len(counts_list)

        if total_products_with_prices > 0:
            buckets = {
                "1": 0, "2-10": 0, "11-50": 0, "51-100": 0,
                "101-200": 0, ">200": 0
            }
            for count in counts_list:
                if count == 1:
                    buckets["1"] += 1
                elif 2 <= count <= 10:
                    buckets["2-10"] += 1
                elif 11 <= count <= 50:
                    buckets["11-50"] += 1
                elif 51 <= count <= 100:
                    buckets["51-100"] += 1
                elif 101 <= count <= 200:
                    buckets["101-200"] += 1
                else:
                    buckets[">200"] += 1
            
            for bucket, count in buckets.items():
                percentage = (count / total_products_with_prices) * 100 if total_products_with_prices > 0 else 0
                self.stdout.write(f"  - Products with {bucket} prices: {count} ({percentage:.2f}%)")

            # Top 10 products with the most prices
            self.stdout.write("\n- Top 10 Products with Highest Price Count:")
            top_10_products = Product.objects.annotate(price_count=Count('prices')).order_by('-price_count')[:10]
            for p in top_10_products:
                self.stdout.write(f"  - \"{p.name}\" (ID: {p.id}): {p.price_count} prices")
        else:
            self.stdout.write("  - No products with prices found to analyze.")

        # === Section 3: Store & Company Analysis ===
        self.stdout.write(self.style.HTTP_INFO('\n[Section 3: Store & Company Analysis]'))

        # Store Count by Company
        self.stdout.write("\n- Store Count by Company:")
        company_store_counts = Company.objects.annotate(store_count=Count('stores')).order_by('-store_count')
        for company in company_store_counts:
            self.stdout.write(f"  - {company.name}: {company.store_count} stores")

        # Anchor Store Status
        self.stdout.write("\n- Anchor Store Status:")
        total_stores = Store.objects.count()
        anchor_store_ids = StoreGroup.objects.filter(anchor__isnull=False).values_list('anchor_id', flat=True).distinct()
        anchor_store_count = len(anchor_store_ids)
        
        if total_stores > 0:
            non_anchor_stores = total_stores - anchor_store_count
            perc_anchor = (anchor_store_count / total_stores) * 100
            self.stdout.write(f"  - Total Stores: {total_stores}")
            self.stdout.write(f"  - Total Anchor Stores: {anchor_store_count} ({perc_anchor:.2f}%)")
            self.stdout.write(f"  - Total Non-Anchor Stores: {non_anchor_stores}")
        else:
            self.stdout.write("  - No stores found in database.")

        self.stdout.write(self.style.SUCCESS('\n--- End of Report ---'))
