from data_management.models import SystemSetting
from products.models import Price


class DefaultCompaniesGenerator:
    """
    Generates and saves the system-wide default company list.
    Saves all company IDs that have any Price rows.
    """
    SETTING_KEY = 'default_pricing_companies'

    def __init__(self, command):
        self.command = command

    def run(self):
        try:
            priced_company_ids = sorted(list(
                Price.objects.values_list('company_id', flat=True).distinct()
            ))

            if not priced_company_ids:
                self.command.stderr.write(self.command.style.ERROR("No companies with price data found."))
                return

            setting, created = SystemSetting.objects.update_or_create(
                key=self.SETTING_KEY,
                defaults={'value': priced_company_ids}
            )

            action = 'Created' if created else 'Updated'
            self.command.stdout.write(self.command.style.SUCCESS(
                f"{action} default company list with {len(priced_company_ids)} companies."
            ))
            self.command.stdout.write(f"Default IDs: {priced_company_ids}")

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred: {str(e)}"))
