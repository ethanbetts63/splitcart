from django.core.management.base import BaseCommand
from companies.models import Company, Store
from django.db.models import Count

class Command(BaseCommand):
    help = 'Debugs company and store data.'

    def add_arguments(self, parser):
        parser.add_argument('--company-name', type=str, help='The name of the company to debug.')

    def handle(self, *args, **options):
        company_name = options['company_name']

        self.stdout.write(self.style.SUCCESS('--- Companies in the database ---'))
        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(self.style.WARNING('No companies found in the database.'))
        else:
            for company in companies:
                self.stdout.write(f'- {company.name} (ID: {company.id})')

        if company_name:
            self.stdout.write(self.style.SUCCESS(f'
--- Debugging company: {company_name} ---'))
            try:
                company = Company.objects.get(name__iexact=company_name)
                self.stdout.write(self.style.SUCCESS(f'Company "{company.name}" found.'))

                stores = Store.objects.filter(company=company).annotate(product_count=Count('prices'))
                if not stores.exists():
                    self.stdout.write(self.style.WARNING(f'No stores found for company "{company.name}".'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Stores for company "{company.name}":'))
                    for store in stores:
                        self.stdout.write(f'- {store.name} (ID: {store.id}), Store ID: {store.store_id}, Product count: {store.product_count}')

            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Company "{company_name}" not found in the database.'))
