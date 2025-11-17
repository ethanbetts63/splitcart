from django.core.management.base import BaseCommand
from companies.models import StoreGroup, Store, Company
from products.models import Product, Price
from django.db.models import Count

class Command(BaseCommand):
    help = 'Inspects Aldi store groups, listing members and their product/price counts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Inspecting ALDI Store Groups ---"))

        try:
            aldi_company = Company.objects.get(name='Aldi')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR("ALDI company not found in the database."))
            return

        aldi_groups = StoreGroup.objects.filter(company=aldi_company).prefetch_related('memberships__store')

        if not aldi_groups.exists():
            self.stdout.write("No ALDI store groups found.")
            return

        for group in aldi_groups:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\nGroup ID: {group.id}"))
            self.stdout.write(f"  Anchor Store: {group.anchor.store_name} (ID: {group.anchor.id})")
            self.stdout.write("  Members:")

            members = [membership.store for membership in group.memberships.all()]
            if not members:
                self.stdout.write("    (No members in this group)")
                continue

            for store in members:
                price_count = Price.objects.filter(store=store).count()
                product_count = Product.objects.filter(prices__store=store).distinct().count()
                
                self.stdout.write(f"    - {store.store_name} (ID: {store.id})")
                self.stdout.write(f"      Products: {product_count}")
                self.stdout.write(f"      Prices: {price_count}")

        self.stdout.write(self.style.SUCCESS("\n--- ALDI Store Group Inspection Complete ---"))
