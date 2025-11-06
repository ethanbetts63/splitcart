from django.core.management.base import BaseCommand
from companies.models import Company

class Command(BaseCommand):
    help = 'Populates the image_url_template field for existing companies.'

    def handle(self, *args, **options):
        company_templates = {
            'coles': 'https://productimages.coles.com.au/productimages/{sku}.jpg',
            'woolworths': 'https://cdn1.woolworths.media/content/wowproductimages/large/{sku}.jpg',
            'iga': 'https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/{sku}.jpg'
        }

        for name, template in company_templates.items():
            try:
                company = Company.objects.get(name__iexact=name)
                company.image_url_template = template
                company.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated {name}'))
            except Company.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Company {name} not found.'))
