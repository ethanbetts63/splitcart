from django.core.management.base import BaseCommand
from companies.models import Company, Category

class Command(BaseCommand):
    help = 'Lists all categories for each company.'

    def handle(self, *args, **options):
        companies = Company.objects.all()
        for company in companies:
            self.stdout.write(self.style.SUCCESS(f"--- {company.name} ---"))
            categories = Category.objects.filter(company=company)
            if categories.exists():
                for category in categories:
                    self.stdout.write(f"  - {category.name}")
            else:
                self.stdout.write(self.style.WARNING("  No categories found."))
