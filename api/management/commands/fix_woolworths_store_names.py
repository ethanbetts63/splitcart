from django.core.management.base import BaseCommand
from companies.models import Store, Company

class Command(BaseCommand):
    help = 'Updates Woolworths stores with name "N/A" to use the suburb as the name.'

    def handle(self, *args, **options):
        try:
            woolworths_company = Company.objects.get(name='Woolworths')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('Company "Woolworths" not found.'))
            return

        stores_to_update = Store.objects.filter(company=woolworths_company, store_name='N/A')
        
        updated_count = 0
        for store in stores_to_update:
            if store.suburb:
                store.store_name = store.suburb
                store.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Updated store {store.store_id} name to "{store.suburb}"'))

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} stores.'))
