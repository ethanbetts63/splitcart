from django.core.management.base import BaseCommand
from companies.models import Company, Category

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            woolworths = Company.objects.get(name__iexact="Aldi")
            category_count = Category.objects.filter(company=woolworths).count()
            print(f"Found {category_count} categories for Woolworths.")
        except Company.DoesNotExist:
            print("Woolworths company not found")
