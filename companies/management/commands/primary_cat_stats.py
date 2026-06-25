from django.core.management.base import BaseCommand
from companies.models import PrimaryCategory
from products.models import Product


class Command(BaseCommand):
    help = 'Reports on product counts per PrimaryCategory using primary_category_slugs.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Primary Category Product Statistics ---'))

        primary_categories = PrimaryCategory.objects.order_by('name')
        if not primary_categories.exists():
            self.stdout.write("  No Primary Categories found.")
            return

        self.stdout.write("\nProducts per Primary Category (via primary_category_slugs):")
        for pc in primary_categories:
            count = Product.objects.filter(primary_category_slugs__contains=[pc.slug]).count()
            self.stdout.write(f"  '{pc.name}' ({pc.slug}): {count} products")

        no_category_count = Product.objects.filter(primary_category_slugs=[]).count()
        self.stdout.write(f"\n  Products with no primary category: {no_category_count}")

        self.stdout.write(self.style.SUCCESS('\n--- Statistics Complete ---'))
