from django.core.management.base import BaseCommand
from companies.models import Store, Postcode
from products.models import Price

class Command(BaseCommand):
    help = 'Lists postcodes that contain at least one store with products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Identifying Postcodes with Products ---"))

        # 1. Get IDs of stores that have at least one Price entry (implying products)
        stores_with_products_ids = Price.objects.values_list('store__id', flat=True).distinct()

        # 2. Get the actual Store objects for these IDs
        stores_with_products = Store.objects.filter(id__in=stores_with_products_ids)

        # 3. Extract unique postcodes from these stores
        postcodes_with_products_str = set(stores_with_products.values_list('postcode', flat=True).distinct())
        postcodes_with_products_str.discard(None) # Remove None entries if any
        postcodes_with_products_str.discard('')    # Remove empty string entries if any

        if postcodes_with_products_str:
            self.stdout.write(self.style.SUCCESS("\nPostcodes containing stores with products:"))
            # Fetch Postcode objects to display more details if available
            postcode_objects = Postcode.objects.filter(postcode__in=postcodes_with_products_str).order_by('postcode')
            
            for postcode_obj in postcode_objects:
                # Count how many stores in this postcode have products
                num_stores = stores_with_products.filter(postcode=postcode_obj.postcode).count()
                self.stdout.write(f"- {postcode_obj.postcode}, {postcode_obj.state} ({postcode_obj.latitude}, {postcode_obj.longitude}) - {num_stores} stores with products")
        else:
            self.stdout.write(self.style.WARNING("\nNo postcodes found with stores that have products."))

        self.stdout.write(self.style.SUCCESS("--- Postcode Identification Complete ---"))
