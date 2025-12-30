from companies.models import Postcode
from data_management.models import SystemSetting
from data_management.utils.geospatial_utils import get_nearby_stores
from products.utils.get_pricing_stores import get_pricing_stores_map

class DefaultStoresGenerator:
    """
    Generates and saves the system-wide default store list.
    """
    SETTING_KEY = 'default_anchor_stores'

    def __init__(self, command):
        self.command = command

    def run(self):
        
        postcode = '6000'
        radius = 15

        try:
            ref_postcode = Postcode.objects.filter(postcode=postcode).first()
            if not ref_postcode:
                self.command.stderr.write(self.command.style.ERROR(f"Postcode {postcode} not found in the database."))
                return

            self.command.stdout.write(f"Finding stores within {radius}km of postcode {postcode}...")
            nearby_stores = get_nearby_stores(ref_postcode, radius)
            
            if not nearby_stores:
                self.command.stderr.write(self.command.style.ERROR("No nearby stores found."))
                return

            store_ids = [store.id for store in nearby_stores]
            self.command.stdout.write(f"Found {len(store_ids)} nearby stores. Determining anchor stores...")

            anchor_map = get_pricing_stores_map(store_ids)
            
            # Get unique anchor store IDs from the map values
            default_anchor_ids = sorted(list(set(anchor_map.values())))

            if not default_anchor_ids:
                self.command.stderr.write(self.command.style.ERROR("Could not determine any anchor stores from the found stores."))
                return

            # Save the list to the SystemSetting model
            setting, created = SystemSetting.objects.update_or_create(
                key=self.SETTING_KEY,
                defaults={'value': default_anchor_ids}
            )

            if created:
                self.command.stdout.write(self.command.style.SUCCESS(f"Successfully created default store list with {len(default_anchor_ids)} anchor stores."))
            else:
                self.command.stdout.write(self.command.style.SUCCESS(f"Successfully updated default store list with {len(default_anchor_ids)} anchor stores."))
            
            self.command.stdout.write(f"Default IDs: {default_anchor_ids}")

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred: {str(e)}"))

