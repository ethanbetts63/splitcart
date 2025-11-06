
from django.core.management.base import BaseCommand
from companies.models import Store
from django.utils import timezone

class Command(BaseCommand):
    help = 'Inspects the scraping-related timestamps for stores of a given company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            required=True,
            help='The name of the company to inspect stores for.'
        )

    def handle(self, *args, **options):
        company_name = options['company']
        self.stdout.write(self.style.SUCCESS(f'--- Inspecting Stores for {company_name} ---'))

        try:
            stores = Store.objects.filter(company__name__iexact=company_name).order_by('pk')
            if not stores.exists():
                self.stdout.write(self.style.WARNING('No stores found for this company.'))
                return

            self.stdout.write(f"Current time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write('-' * 80)

            for store in stores:
                last_scraped_str = store.last_scraped.strftime('%Y-%m-%d %H:%M:%S') if store.last_scraped else 'Never'
                scheduled_at_str = store.scheduled_at.strftime('%Y-%m-%d %H:%M:%S') if store.scheduled_at else 'Never'
                
                self.stdout.write(
                    f"  PK: {store.pk:<5} | Name: {store.store_name:<25} | Last Scraped: {last_scraped_str:<20} | Scheduled At: {scheduled_at_str}"
                )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
