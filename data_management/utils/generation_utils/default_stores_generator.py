from data_management.models import SystemSetting
from products.models import Price

class DefaultStoresGenerator:
    """
    Generates and saves the system-wide default store list.
    Saves all store IDs that have any Price rows — one per company in practice.
    """
    SETTING_KEY = 'default_anchor_stores'

    def __init__(self, command):
        self.command = command

    def run(self):
        try:
            priced_store_ids = sorted(list(
                Price.objects.values_list('store_id', flat=True).distinct()
            ))

            if not priced_store_ids:
                self.command.stderr.write(self.command.style.ERROR("No stores with price data found."))
                return

            setting, created = SystemSetting.objects.update_or_create(
                key=self.SETTING_KEY,
                defaults={'value': priced_store_ids}
            )

            action = 'Created' if created else 'Updated'
            self.command.stdout.write(self.command.style.SUCCESS(
                f"{action} default store list with {len(priced_store_ids)} stores."
            ))
            self.command.stdout.write(f"Default IDs: {priced_store_ids}")

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred: {str(e)}"))
